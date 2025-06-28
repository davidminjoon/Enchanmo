from __future__ import annotations
from godok import Godok

from copy import deepcopy
from datetime import datetime
import os
import shutil
import subprocess
import sys
from functools import partial

from PIL import Image
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QFrame, \
    QTabWidget, QLabel, QPushButton, QRadioButton, QComboBox, QDateEdit, QCheckBox, QSizePolicy, QAction, \
    QDialog, QLineEdit, QFileDialog, QLayout, QMessageBox, QButtonGroup, QSpinBox, QScrollArea, QProgressBar
from PyQt5.QtGui import QFont, QPixmap, QImage
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal

qimage = None


class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    result_ready = pyqtSignal(object)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        self.result = self.func(self.progress_updated.emit, *self.args, **self.kwargs)
        self.result_ready.emit(self.result)
        self.finished.emit()


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("진행 중...")

        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.label = QLabel("처리 중입니다...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setRange(0, 100)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def update_progress(self, value):
        self.progress_bar.setValue(value)


class GodokAssistant(QMainWindow):
    class EditBanHomma(QDialog):
        def __init__(self, godok: Godok):
            super().__init__()
            self.godok = godok

            # Highest object hierarchy
            self.bigVLayout = QVBoxLayout()
            self.setLayout(self.bigVLayout)

            # Components for bigVLayout
            self.headerLabel = QLabel("금지 홈마 편집", self)
            self.headerLabel.setAlignment(Qt.AlignCenter)
            self.scrollArea = QScrollArea(self)
            self.scrollArea.setMaximumHeight(700)
            self.scrollArea.setMinimumWidth(500)
            self.confirmButton = QPushButton("변경사항 저장하기", self)
            self.confirmButton.released.connect(self.updateBanHommas)

            self.banHommaEditHDivider = QFrame(self)
            self.banHommaEditHDivider.setFrameShape(QFrame.HLine)
            self.banHommaEditHDivider.setFrameShadow(QFrame.Sunken)

            # Layout settings for bigVLayout
            self.bigVLayout.addWidget(self.headerLabel)
            self.bigVLayout.addWidget(self.banHommaEditHDivider)
            self.bigVLayout.addWidget(self.scrollArea)
            self.bigVLayout.addWidget(self.confirmButton)

            # Components & Layout settings for scrollArea
            self.browseGLayout = QGridLayout()
            self.scrollArea.setLayout(self.browseGLayout)

            # Components & Layout settings for browseGLayout
            self.bannedHeaderLabel = QLabel("금홈", self)
            self.hommaNameHeaderLabel = QLabel("홈마", self)
            self.photoCountHeaderLabel = QLabel("사진 개수", self)

            self.hommaBrowseList = [(homma in self.godok.banned_hommas, homma, len(self.godok.homma_to_photo[homma]))
                                    for homma in sorted(self.godok.hommas)]
            self.checklist = [QCheckBox(self) for _ in self.godok.hommas]

            self.browseGLayout.addWidget(self.bannedHeaderLabel, 0, 0)
            self.browseGLayout.addWidget(self.hommaNameHeaderLabel, 0, 1)
            self.browseGLayout.setColumnStretch(2, 1)
            self.browseGLayout.addWidget(self.photoCountHeaderLabel, 0, 3)

            for i in range(len(self.godok.hommas)):
                isban, homma, count = self.hommaBrowseList[i]
                self.checklist[i].setChecked(isban)
                if homma == '(알 수 없음)': self.checklist[i].setEnabled(False)
                self.browseGLayout.addWidget(self.checklist[i], i + 1, 0)
                self.browseGLayout.addWidget(QLabel(f'@{homma}', self), i + 1, 1)
                self.browseGLayout.addWidget(QLabel(str(count), self), i + 1, 3)

            self.browseGLayout.setRowStretch(len(self.godok.hommas) + 1, 1)

        def updateBanHommas(self):
            self.godok.banned_hommas = [self.hommaBrowseList[i][1] for i in range(len(self.godok.hommas))
                                        if self.checklist[i].isChecked()]
            self.close()

    class SimilarityDialog(QDialog):
        def __init__(self, superUI: GodokAssistant):
            super().__init__()
            self.superUI: GodokAssistant = superUI
            self.godok: Godok = self.superUI.godok
            self.query_pillow: Image.Image | None = None
            self.setWindowTitle("유사한 사진 검색")

            # Highest object hierarchy
            self.bigHLayout = QHBoxLayout()
            self.setLayout(self.bigHLayout)
            self.bigHLayout.setSizeConstraint(QLayout.SetFixedSize)

            # Components for bigHLayout
            self.settingGLayout = QGridLayout()
            self.bigVDivider = QFrame(self)
            self.bigVDivider.setFrameShape(QFrame.VLine)
            self.bigVDivider.setFrameShadow(QFrame.Sunken)

            self.imageDisplayPixmapLabel = QLabel("(이미지 없음)", self)
            self.imageDisplayPixmapLabel.setAlignment(Qt.AlignCenter)
            self.imageDisplayPixmapLabel.setFixedSize(400, 600)

            # Layout settings for bigHLayout
            self.bigHLayout.addLayout(self.settingGLayout)
            self.bigHLayout.addWidget(self.bigVDivider)
            self.bigHLayout.addWidget(self.imageDisplayPixmapLabel)

            # Components for settingGLayout
            self.hommaSettingLabel = QLabel("홈마 설정", self)
            self.hommaSettingVDivider = QFrame(self)
            self.hommaSettingVDivider.setFrameShape(QFrame.VLine)
            self.hommaSettingVDivider.setFrameShadow(QFrame.Sunken)

            self.hommaAllRadio = QRadioButton("모든 홈마", self)
            self.hommaAllRadio.clicked.connect(self.validateRadioboxCombination)
            self.hommaNoRadio = QRadioButton("금홈 제외", self)
            self.hommaNoRadio.clicked.connect(self.validateRadioboxCombination)
            self.hommaOnlyRadio = QRadioButton("금홈만", self)
            self.hommaOnlyRadio.clicked.connect(self.validateRadioboxCombination)
            self.hommaButtonGroup = QButtonGroup(self)
            self.hommaButtonGroup.setExclusive(True)
            self.hommaButtonGroup.addButton(self.hommaOnlyRadio)
            self.hommaButtonGroup.addButton(self.hommaNoRadio)
            self.hommaButtonGroup.addButton(self.hommaAllRadio)

            self.bubbleSettingLabel = QLabel("버블 설정", self)
            self.bubbleSettingVDivider = QFrame(self)
            self.bubbleSettingVDivider.setFrameShape(QFrame.VLine)
            self.bubbleSettingVDivider.setFrameShadow(QFrame.Sunken)

            self.bubbleAllRadio = QRadioButton("버블 포함", self)
            self.bubbleAllRadio.clicked.connect(self.validateRadioboxCombination)
            self.bubbleNoRadio = QRadioButton("버블 제외", self)
            self.bubbleNoRadio.clicked.connect(self.validateRadioboxCombination)
            self.bubbleOnlyRadio = QRadioButton("버블만", self)
            self.bubbleOnlyRadio.clicked.connect(self.validateRadioboxCombination)
            self.bubbleButtonGroup = QButtonGroup(self)
            self.bubbleButtonGroup.setExclusive(True)
            self.bubbleButtonGroup.addButton(self.bubbleOnlyRadio)
            self.bubbleButtonGroup.addButton(self.bubbleNoRadio)
            self.bubbleButtonGroup.addButton(self.bubbleAllRadio)

            self.hommaNoRadio.setChecked(True)
            self.bubbleNoRadio.setChecked(True)

            self.resultCountLabel = QLabel("검색 결과 개수", self)
            self.resultCountSettingVDivider = QFrame(self)
            self.resultCountSettingVDivider.setFrameShape(QFrame.VLine)
            self.resultCountSettingVDivider.setFrameShadow(QFrame.Sunken)
            self.resultCountSpinbox = QSpinBox(self)
            self.resultCountSpinbox.setMinimum(1)

            self.importSettingLabel = QLabel("검색 대상 불러오기", self)
            self.importSettingVDivider = QFrame(self)
            self.importSettingVDivider.setFrameShape(QFrame.VLine)
            self.importSettingVDivider.setFrameShadow(QFrame.Sunken)
            self.importFromExplorerButton = QPushButton("파일 찾기", self)
            self.importFromExplorerButton.released.connect(self.importFromExplorerReact)
            self.importFromClipboardButton = QPushButton("클립보드", self)
            self.importFromClipboardButton.released.connect(self.importFromClipboardReact)
            self.searchInitButton = QPushButton("검색 시작", self)
            self.searchInitButton.released.connect(self.initSearchReact)

            # Layout settings for settingGLayout
            self.settingGLayout.addWidget(self.hommaSettingLabel, 0, 0)
            self.settingGLayout.addWidget(self.hommaSettingVDivider, 0, 1)
            self.settingGLayout.addWidget(self.hommaAllRadio, 0, 2)
            self.settingGLayout.addWidget(self.hommaNoRadio, 0, 3)
            self.settingGLayout.addWidget(self.hommaOnlyRadio, 0, 4)

            self.settingGLayout.addWidget(self.bubbleSettingLabel, 1, 0)
            self.settingGLayout.addWidget(self.bubbleSettingVDivider, 1, 1)
            self.settingGLayout.addWidget(self.bubbleAllRadio, 1, 2)
            self.settingGLayout.addWidget(self.bubbleNoRadio, 1, 3)
            self.settingGLayout.addWidget(self.bubbleOnlyRadio, 1, 4)

            self.settingGLayout.setRowStretch(2, 1)

            self.settingGLayout.addWidget(self.resultCountLabel, 3, 0)
            self.settingGLayout.addWidget(self.resultCountSettingVDivider, 3, 1)
            self.settingGLayout.addWidget(self.resultCountSpinbox, 3, 2)

            self.settingGLayout.addWidget(self.importSettingLabel, 4, 0)
            self.settingGLayout.addWidget(self.importSettingVDivider, 4, 1)
            self.settingGLayout.addWidget(self.importFromExplorerButton, 4, 2)
            self.settingGLayout.addWidget(self.importFromClipboardButton, 4, 3)
            self.settingGLayout.addWidget(self.searchInitButton, 4, 4)

            self.validateRadioboxCombination()

        def importFromExplorerReact(self):
            fname = QFileDialog.getOpenFileName(self, "검색 대상 찾기")
            if not fname[0]: return
            self.query_pillow = Image.open(fname[0])
            self.updateQueryDisplay()

        def importFromClipboardReact(self):
            self.query_pillow = GodokAssistant.pillow_from_clipboard()
            self.updateQueryDisplay()

        def validateRadioboxCombination(self):
            if self.query_pillow is None:
                self.searchInitButton.setEnabled(False)
                return
            if self.hommaOnlyRadio.isChecked() and self.bubbleOnlyRadio.isChecked():
                self.searchInitButton.setEnabled(False)
                return
            self.searchInitButton.setEnabled(True)

        def updateQueryDisplay(self):
            self.validateRadioboxCombination()
            if self.query_pillow is None:
                self.imageDisplayPixmapLabel.setText('(이미지 없음)')
                return

            __imgdat = self.query_pillow.convert('RGBA').tobytes('raw', 'BGRA')
            __qim = QImage(__imgdat, self.query_pillow.width, self.query_pillow.height, QImage.Format_ARGB32)
            pixmap = QPixmap.fromImage(__qim).scaled(400, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.imageDisplayPixmapLabel.setPixmap(pixmap)

        def initSearchReact(self):
            homma_scope = []
            if self.hommaOnlyRadio.isChecked():
                homma_scope.extend(self.godok.banned_hommas)
            elif self.bubbleOnlyRadio.isChecked():
                homma_scope.extend(self.godok.bubble_paths)
            else:
                if self.hommaNoRadio.isChecked():
                    homma_scope.extend(self.godok.safe_hommas)
                elif self.hommaAllRadio.isChecked():
                    homma_scope.extend(self.godok.hommas)
                if self.bubbleAllRadio.isChecked(): homma_scope.extend(self.godok.bubble_paths)

            search_scope = []
            for homma in homma_scope:
                search_scope.extend(self.godok.homma_to_photo[homma])

            __qpix, __qsvd = Godok.pixsvd_from_pillow(self.query_pillow)
            __rank = self.godok.norm_rank(__qpix, __qsvd, search_scope)[:self.resultCountSpinbox.value()]
            self.close()
            self.superUI.viewDetailDialog(__rank, self.godok.get_metalist(__rank), '')

    class ScrapeDialog(QDialog):
        def __init__(self, superUI):
            super().__init__()
            self.superUI: GodokAssistant = superUI
            self.savedir = ''
            self.url = ''
            self.setWindowTitle("X(트위터)에서 가져오기")

            # Highest object hierarchy
            self.bigGLayout = QGridLayout()
            self.setLayout(self.bigGLayout)
            self.bigGLayout.setSizeConstraint(QLayout.SetFixedSize)

            # Components for bigGLayout
            self.urlLabel = QLabel("X(트위터) 게시물 주소", self)
            self.urlLineEdit = QLineEdit(self)
            self.urlLineEdit.setFont(QFont("SUITE", 7))
            self.urlLineEdit.setMinimumWidth(700)
            self.urlLineEdit.textEdited.connect(self.changedText)
            self.saveDirLabel = QLabel("저장 위치", self)

            self.saveDirBrowseButton = QPushButton("...", self)
            self.saveDirBrowseButton.setFixedWidth(50)
            self.saveDirDisplayLabel = QLabel(self)
            self.saveDirDisplayLabel.setFont(QFont("SUITE", 7))
            self.saveDirBrowseButton.pressed.connect(self.browseSaveDir)

            self.browseInitButton = QPushButton("사진 가져오기", self)
            self.browseInitButton.pressed.connect(self.browseInit)
            self.errInfo = QLabel(self)

            # Layout settings for bigGLayout
            self.bigGLayout.addWidget(self.urlLabel, 0, 0)
            self.bigGLayout.addWidget(self.urlLineEdit, 0, 1)
            self.bigGLayout.addWidget(self.saveDirLabel, 1, 0)
            self.bigGLayout.addWidget(self.saveDirDisplayLabel, 1, 1)
            self.bigGLayout.addWidget(self.saveDirBrowseButton, 1, 2)
            self.bigGLayout.addWidget(self.browseInitButton, 2, 0)
            self.bigGLayout.addWidget(self.errInfo, 2, 1)

            self.validateForm()

        def changedText(self):
            self.url = self.urlLineEdit.text()
            self.validateForm()

        def browseSaveDir(self):
            fname = QFileDialog.getExistingDirectory(self, '다운로드받을 위치 설정')
            self.savedir = fname
            if not fname: return
            self.saveDirDisplayLabel.setText(fname)
            self.validateForm()

        def validateForm(self):
            def __validateForm() -> tuple[bool, str]:
                if len(self.urlLineEdit.text()) == 0: return False, "X(트위터) 링크를 복사해주세요."
                if not self.urlLineEdit.text().startswith("https://x.com/"):
                    return False, "X(트위터)가 아닌 링크는 사용할 수 없습니다."
                if len(self.saveDirDisplayLabel.text()) == 0: return False, "이미지를 저장할 위치를 선택해주세요."
                return True, "왼쪽 버튼을 눌러주세요!"

            res, msg = __validateForm()
            self.browseInitButton.setEnabled(res)
            self.errInfo.setStyleSheet(f"Color : {'blue' if res else 'red'}")
            self.errInfo.setText(msg)

        def __browseInitInternal(self, progress_callback):
            return self.superUI.godok.scrape_tweet(progress_callback, self.url, self.savedir)

        def __browseInitResHandle(self, retrieve):
            if len(retrieve[0]) == 0:
                QMessageBox.warning(self, "찾은 사진 없음", "주어진 링크에서 사진을 찾을 수 없었습니다."
                                                      "가져오고자 하는 트윗이 공개 트윗인지, 사진이 있는지"
                                                      "확인 후 다시 시도해주세요. 문제가 지속될 경우 개발자에게"
                                                      "문의 부탁드립니다!", QMessageBox.Ok)
                return
            self.superUI.viewDetailDialog(*retrieve)

        def browseInit(self):
            try:
                __progressbar = ProgressDialog(self)
                __worker = WorkerThread(self.__browseInitInternal)
                __worker.progress_updated.connect(__progressbar.update_progress)
                __worker.finished.connect(__progressbar.accept)
                __worker.result_ready.connect(self.__browseInitResHandle)

                __worker.start()
                __progressbar.exec_()

            except Exception as e:
                QMessageBox.critical(self, "오류 발생", f"사진을 불러오던 중 오류가 발생했습니다."
                                                    f"가져오고자 하는 트윗이 공개 트윗인지, 저장 폴더에 문제가 없는지,"
                                                    f"인터넷 연결이 원활한지 확인한 후 다시 시도해주세요. "
                                                    f"문제가 지속될 경우 개발자에게 문의 부탁드립니다! "
                                                    f"(에러 메세지: {e})", QMessageBox.Ok)
                return

            finally:
                self.close()

    class DetailDialog(QDialog):
        def __init__(self, loadDirList: list[str], metadata: list[dict], desc: str, godok: Godok):
            super().__init__()
            self.loadDirList = loadDirList
            self.godok = godok
            self.imageIndex = 0
            self.metadata_collect = deepcopy(metadata)
            self.init_complete = False

            # Highest object hierarchy
            self.bigHLayout = QHBoxLayout()
            self.setLayout(self.bigHLayout)
            self.bigHLayout.setSizeConstraint(QLayout.SetFixedSize)

            # Components for bigHLayout
            self.imageViewVLayout = QVBoxLayout()

            self.imageViewVDivider = QFrame(self)
            self.imageViewVDivider.setFrameShape(QFrame.VLine)
            self.imageViewVDivider.setFrameShadow(QFrame.Sunken)

            self.infoEditGLayout = QGridLayout()

            # Layout settings for bigHLayout
            self.bigHLayout.addLayout(self.imageViewVLayout)
            self.bigHLayout.addWidget(self.imageViewVDivider)
            self.bigHLayout.addLayout(self.infoEditGLayout)

            # Components for imageViewVLayout
            self.imageDisplayLabel = QLabel(self)
            self.imageDisplayLabel.setFixedWidth(600)
            self.imageDisplayLabel.setAlignment(Qt.AlignHCenter)
            self.imageDescriptionLabel = QLabel(self)
            self.imageDescriptionLabel.setAlignment(Qt.AlignCenter)
            self.imageMoveHLayout = QHBoxLayout()

            # Layout settings for imageViewVLayout
            self.imageViewVLayout.addLayout(self.imageMoveHLayout)
            self.imageViewVLayout.addWidget(self.imageDisplayLabel)
            self.imageViewVLayout.addStretch(1)
            self.imageViewVLayout.addWidget(self.imageDescriptionLabel)

            # Components for imageMoveHLayout
            self.leftButton = QPushButton("◀", self)
            self.leftButton.setMaximumWidth(80)
            self.leftButton.setFlat(True)
            self.leftButton.pressed.connect(partial(self.transitionPixmap, True))
            self.currentLabel = QLabel(self)

            self.rightButton = QPushButton("▶", self)
            self.rightButton.setMaximumWidth(80)
            self.rightButton.setFlat(True)
            self.rightButton.pressed.connect(partial(self.transitionPixmap, False))

            # Layout settings for imageMoveHLayout
            self.imageMoveHLayout.addWidget(self.leftButton)
            self.imageMoveHLayout.addStretch(1)
            self.imageMoveHLayout.addWidget(self.currentLabel)
            self.imageMoveHLayout.addStretch(1)
            self.imageMoveHLayout.addWidget(self.rightButton)

            # Components for infoEditGLayout
            self.sourceLabel = QLabel("출처(링크)", self)
            self.memberLabel = QLabel("멤버", self)
            self.hommaLabel = QLabel("홈마", self)
            self.dateLabel = QLabel("촬영 날짜", self)
            self.tagLabel = QLabel("태그(최대 6개)", self)
            self.originalDirectoryLabel = QLabel("원본 저장 위치", self)

            self.sourceLineEdit = QLineEdit(self)
            self.sourceLineEdit.setFont(QFont("SUITE", 7))
            self.sourceLineEdit.setMaximumWidth(700)
            self.sourceLineEdit.textEdited.connect(self.updateMetadata)

            self.memberButtonGLayout = QGridLayout()
            self.hommaSettingHLayout = QHBoxLayout()
            self.shootDateEdit = QDateEdit(self)
            self.shootDateEdit.dateChanged.connect(self.updateMetadata)
            self.shootDateEdit.setDate(QDate.currentDate())
            self.tagGLayout = QGridLayout()
            self.originalDirectoryDisplayLabel = QLabel(self)
            self.originalDirectoryDisplayLabel.setFont(QFont("SUITE", 7))
            self.miscSettingGLayout = QGridLayout()

            # Layout settings for infoEditGLayout
            self.infoEditGLayout.addWidget(self.sourceLabel, 0, 0)
            self.infoEditGLayout.addWidget(self.sourceLineEdit, 0, 1)
            self.infoEditGLayout.addWidget(self.memberLabel, 1, 0)
            self.infoEditGLayout.addLayout(self.memberButtonGLayout, 1, 1)
            self.infoEditGLayout.addWidget(self.hommaLabel, 2, 0)
            self.infoEditGLayout.addLayout(self.hommaSettingHLayout, 2, 1)
            self.infoEditGLayout.addWidget(self.dateLabel, 3, 0)
            self.infoEditGLayout.addWidget(self.shootDateEdit, 3, 1)
            self.infoEditGLayout.addWidget(self.tagLabel, 4, 0)
            self.infoEditGLayout.addLayout(self.tagGLayout, 4, 1)
            self.infoEditGLayout.addWidget(self.originalDirectoryLabel, 5, 0)
            self.infoEditGLayout.addWidget(self.originalDirectoryDisplayLabel, 5, 1)
            self.infoEditGLayout.setRowStretch(6, 1)
            self.infoEditGLayout.addLayout(self.miscSettingGLayout, 7, 1)

            # Components for memberButtonGLayout
            self.lilyButton = QPushButton("릴리", self)
            self.lilyButton.setCheckable(True)
            self.lilyButton.released.connect(self.updateMetadata)

            self.haewonButton = QPushButton("해원", self)
            self.haewonButton.setCheckable(True)
            self.haewonButton.released.connect(self.updateMetadata)

            self.sullyoonButton = QPushButton("설윤", self)
            self.sullyoonButton.setCheckable(True)
            self.sullyoonButton.released.connect(self.updateMetadata)

            self.baeButton = QPushButton("배이", self)
            self.baeButton.setCheckable(True)
            self.baeButton.released.connect(self.updateMetadata)

            self.jiwooButton = QPushButton("지우", self)
            self.jiwooButton.setCheckable(True)
            self.jiwooButton.released.connect(self.updateMetadata)

            self.kyujinButton = QPushButton("규진", self)
            self.kyujinButton.setCheckable(True)
            self.kyujinButton.released.connect(self.updateMetadata)

            # Layout settings for memberButtonGLayout
            self.memberButtonGLayout.addWidget(self.lilyButton, 0, 0)
            self.memberButtonGLayout.addWidget(self.haewonButton, 0, 1)
            self.memberButtonGLayout.addWidget(self.sullyoonButton, 0, 2)
            self.memberButtonGLayout.addWidget(self.baeButton, 1, 0)
            self.memberButtonGLayout.addWidget(self.jiwooButton, 1, 1)
            self.memberButtonGLayout.addWidget(self.kyujinButton, 1, 2)

            # Components for hommaSettingHLayout
            self.hommaManualEdit = QLineEdit(self)
            self.hommaManualEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.hommaManualEdit.textEdited.connect(self.updateMetadata)

            self.hommaSelectComboBox = QComboBox(self)
            __homma_list = sorted(self.godok.hommas)
            self.hommaSelectComboBox.addItems(__homma_list)
            self.hommaSelectComboBox.activated.connect(self.setHommaCombobox)
            try:
                self.hommaSelectComboBox.setCurrentIndex(__homma_list.index(
                    metadata[self.imageIndex].get('homma', '(알 수 없음)')))
            except ValueError:
                self.hommaSelectComboBox.setCurrentIndex(__homma_list.index('(알 수 없음)'))

            # Layout settings for hommaSettingHLayout
            self.hommaSettingHLayout.addWidget(self.hommaManualEdit)
            self.hommaSettingHLayout.addWidget(self.hommaSelectComboBox)

            # Components for tagGLayout
            self.tagManualEditList = [QLineEdit(self) for _ in range(6)]

            # Layout settings for tagGLayout
            for i in range(6):
                self.tagGLayout.addWidget(self.tagManualEditList[i], *divmod(i, 2))
                self.tagManualEditList[i].textEdited.connect(self.updateMetadata)

            # Components for miscSettingGLayout
            self.locateInExplorer = QPushButton("현재 사진의 원본 위치로 이동", self)
            self.locateInExplorer.released.connect(self.locateInExplorerReact)
            self.copyToClipboard = QPushButton("이 사진 클립보드로 복사하기", self)
            self.copyToClipboard.released.connect(self.copyToClipboardReact)
            self.exportToExplorer = QPushButton("내보내기", self)
            self.exportToExplorer.released.connect(self.exportToExplorerReact)
            self.copyToAllCheckbox = QCheckBox("모든 사진에 현재 페이지의 내용 적용", self)
            self.completeButton = QPushButton("변경사항 저장", self)
            self.completeButton.pressed.connect(self.sendToGodok)

            # Layout settings for miscSettingGLayout
            self.miscSettingGLayout.addWidget(self.copyToClipboard, 0, 0)
            self.miscSettingGLayout.addWidget(self.locateInExplorer, 1, 0)
            self.miscSettingGLayout.addWidget(self.exportToExplorer, 1, 1)
            self.miscSettingGLayout.addWidget(self.copyToAllCheckbox, 2, 0)
            self.miscSettingGLayout.addWidget(self.completeButton, 2, 1)

            # Dialog initial logic
            self.loadPixmap(0)
            if len(desc) > 0: self.imageDescriptionLabel.setText(desc[:20] + ('...' if len(desc) > 20 else ''))

            # Editor logic
            self.loadMetadata()
            self.init_complete = True

        def locateInExplorerReact(self):
            target_path = self.loadDirList[self.imageIndex].replace('/', '\\')
            subprocess.Popen(f'explorer /select,"{target_path}"')

        def copyToClipboardReact(self):
            GodokAssistant.copy_image_to_clipboard(self.loadDirList[self.imageIndex])

        def exportToExplorerReact(self):
            __sto_abs_path = os.path.abspath('./sto/')
            for __filename in os.listdir(__sto_abs_path):
                if __filename.startswith('godok_helper'):
                    os.remove(os.path.join(__sto_abs_path, __filename))

            source_set = set()
            for __idx in range(len(self.loadDirList)):
                __path = self.loadDirList[__idx]
                shutil.copy(__path, os.path.join(__sto_abs_path, f'godok_helper_{__idx + 1}.png'))
                if len(__source := self.metadata_collect[__idx]['source']) > 0:
                    source_set.add(__source)

            with open(os.path.join(__sto_abs_path, f'godok_helper_sources.txt'), 'w', encoding='utf-8') as f:
                f.write('\n'.join(source_set))

            os.startfile(__sto_abs_path)

        def setHommaCombobox(self):
            self.hommaManualEdit.setText(self.hommaSelectComboBox.currentText())
            self.updateMetadata()

        def loadMetadata(self):
            __local_metadata = self.metadata_collect[self.imageIndex]

            self.sourceLineEdit.setText(__local_metadata.get('source', ''))
            __member_meta = __local_metadata.get('members', 0)

            self.lilyButton.setChecked(bool(__member_meta & (1 << 5)))
            self.haewonButton.setChecked(bool(__member_meta & (1 << 4)))
            self.sullyoonButton.setChecked(bool(__member_meta & (1 << 3)))
            self.baeButton.setChecked(bool(__member_meta & (1 << 2)))
            self.jiwooButton.setChecked(bool(__member_meta & (1 << 1)))
            self.kyujinButton.setChecked(bool(__member_meta & (1 << 0)))
            self.hommaManualEdit.setText(__local_metadata.get('homma', '(알 수 없음)'))
            self.shootDateEdit.setDate(
                QDate(*__local_metadata.get('date')) if 'date' in __local_metadata.keys() else QDate.currentDate())
            for edit, tag in zip(self.tagManualEditList, __local_metadata.get('tags', [''] * 6)): edit.setText(tag)

            __orgdir = __local_metadata.get('dir', '')
            self.originalDirectoryDisplayLabel.setText(('...' if len(__orgdir) > 60 else '') + __orgdir[-60:])

        def transitionPixmap(self, left: bool):
            if left: return self.loadPixmap(max(0, self.imageIndex - 1))
            return self.loadPixmap(min(len(self.loadDirList) - 1, self.imageIndex + 1))

        def loadPixmap(self, index: int):
            pixmap = QPixmap(self.loadDirList[index]).scaled(600, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.imageDisplayLabel.setPixmap(pixmap)
            self.currentLabel.setText(f'{index + 1} / {len(self.loadDirList)}')
            self.imageIndex = index

            self.leftButton.setEnabled(True)
            self.rightButton.setEnabled(True)
            if index == 0: self.leftButton.setEnabled(False)
            if index == len(self.loadDirList) - 1: self.rightButton.setEnabled(False)

            self.imageDescriptionLabel.setText(os.path.split(self.loadDirList[index])[1])
            self.loadMetadata()

        def updateMetadata(self):
            if not self.init_complete: return
            __local_old = self.metadata_collect[self.imageIndex]
            __new = {'source': self.sourceLineEdit.text(),
                     'members': self.lilyButton.isChecked() * 32
                                + self.haewonButton.isChecked() * 16
                                + self.sullyoonButton.isChecked() * 8
                                + self.baeButton.isChecked() * 4
                                + self.jiwooButton.isChecked() * 2
                                + self.kyujinButton.isChecked(),
                     'homma': self.hommaManualEdit.text(),
                     'date': (self.shootDateEdit.date().year(),
                              self.shootDateEdit.date().month(),
                              self.shootDateEdit.date().day()),
                     'tags': [__edit.text() for __edit in self.tagManualEditList],
                     'dir': __local_old['dir']}
            self.metadata_collect[self.imageIndex] = __new

        def sendToGodok(self):
            __progressbar = ProgressDialog(self)
            __worker = WorkerThread(self.__sendToGodokInternal)
            __worker.progress_updated.connect(__progressbar.update_progress)
            __worker.finished.connect(__progressbar.accept)

            __worker.start()
            __progressbar.exec_()

        def __sendToGodokInternal(self, progress_callback):
            for i, (__path, __meta) in enumerate(zip(self.loadDirList, self.metadata_collect)):
                if self.copyToAllCheckbox.isChecked():
                    self.godok.add_entry(__path, self.metadata_collect[self.imageIndex])
                else:
                    self.godok.add_entry(__path, __meta)
                progress_callback(((i + 1) * 100) // len(self.loadDirList))

            self.godok.export()
            self.close()

    def __init__(self):
        super().__init__()
        self.godok = Godok()

        # Visual aspects
        QApplication.setFont(QFont("SUITE", 10))

        # Initiator functions
        self.initUI()
        self.initBar()
        self.initLogic()

        # Geometry
        self.setWindowTitle("고독방 도우미")
        self.setGeometry(100, 100, 636, 480)
        self.show()

    # noinspection PyAttributeOutsideInit
    def initUI(self):
        # Components for bigHLayout
        self.searchSettingVLayout = QVBoxLayout()
        self.scaffoldCentralWidget = QWidget(self)
        self.scaffoldCentralWidget.setLayout(self.searchSettingVLayout)
        self.setCentralWidget(self.scaffoldCentralWidget)

        # Components for searchSettingVLayout
        self.searchSettingLabel = QLabel("사진 검색 조건 설정")
        self.searchSettingLabel.setAlignment(Qt.AlignCenter)

        self.searchSettingTopHDivider = QFrame(self)
        self.searchSettingTopHDivider.setFrameShape(QFrame.HLine)
        self.searchSettingTopHDivider.setFrameShadow(QFrame.Sunken)

        self.searchTabWidget = QTabWidget(self)
        self.searchInitHLayout = QHBoxLayout()

        self.searchSettingMiddleHDivider = QFrame(self)
        self.searchSettingMiddleHDivider.setFrameShape(QFrame.HLine)
        self.searchSettingMiddleHDivider.setFrameShadow(QFrame.Sunken)

        self.statsGLayout = QGridLayout()

        self.searchSettingBottomHDivider = QFrame(self)
        self.searchSettingBottomHDivider.setFrameShape(QFrame.HLine)
        self.searchSettingBottomHDivider.setFrameShadow(QFrame.Sunken)

        self.creditsNameLabel = QLabel('"따스한 엔써" © 무단 재배포 금지', self)
        self.creditsNameLabel.setAlignment(Qt.AlignCenter)
        self.creditsChatroomLabel = QLabel("[엔써들의 찬란한 모임 & 엔끌벅적 엔써들의 소통방]", self)
        self.creditsChatroomLabel.setAlignment(Qt.AlignCenter)
        self.creditsVersionLabel = QLabel("ver 1.0.0 / 2025.06.23.", self)
        self.creditsVersionLabel.setAlignment(Qt.AlignCenter)

        # Layout settings for searchSettingVLayout
        self.searchSettingVLayout.addWidget(self.searchSettingLabel)
        self.searchSettingVLayout.addWidget(self.searchSettingTopHDivider)
        self.searchSettingVLayout.addWidget(self.searchTabWidget)
        self.searchSettingVLayout.addLayout(self.searchInitHLayout)
        self.searchSettingVLayout.addWidget(self.searchSettingMiddleHDivider)
        self.searchSettingVLayout.addLayout(self.statsGLayout)
        self.searchSettingVLayout.addWidget(self.creditsNameLabel)
        self.searchSettingVLayout.addWidget(self.searchSettingBottomHDivider)
        self.searchSettingVLayout.addWidget(self.creditsNameLabel)
        self.searchSettingVLayout.addWidget(self.creditsChatroomLabel)
        self.searchSettingVLayout.addWidget(self.creditsVersionLabel)

        # Components for searchInitHLayout
        self.searchSettingResetButton = QPushButton("검색 조건 초기화", self)
        self.searchSettingResetButton.released.connect(self.resetSettings)
        self.searchInitButton = QPushButton("검색 시작", self)
        self.searchInitButton.released.connect(self.initSearch)

        # Layout settings for searchInitHLayout
        self.searchInitHLayout.addWidget(self.searchSettingResetButton)
        self.searchInitHLayout.addWidget(self.searchInitButton)

        # Components for statsGLayout
        self.sharableCountLabel = QLabel("공유 가능한 사진 개수", self)
        self.totalCountLabel = QLabel("총 사진 개수", self)
        self.hommaCountLabel = QLabel("홈마 수", self)
        self.sharableCountValueLabel = QLabel(self)
        self.totalCountValueLabel = QLabel(self)
        self.hommaCountValueLabel = QLabel(self)

        self.statsTopVDivider = QFrame(self)
        self.statsTopVDivider.setFrameShape(QFrame.VLine)
        self.statsTopVDivider.setFrameShadow(QFrame.Sunken)

        self.statsMiddleVDivider = QFrame(self)
        self.statsMiddleVDivider.setFrameShape(QFrame.VLine)
        self.statsMiddleVDivider.setFrameShadow(QFrame.Sunken)

        self.statsBottomVDivider = QFrame(self)
        self.statsBottomVDivider.setFrameShape(QFrame.VLine)
        self.statsBottomVDivider.setFrameShadow(QFrame.Sunken)

        # Layout settings for statsGLayout
        self.statsGLayout.addWidget(self.sharableCountLabel, 0, 0)
        self.statsGLayout.addWidget(self.statsTopVDivider, 0, 1)
        self.statsGLayout.addWidget(self.sharableCountValueLabel, 0, 2)

        self.statsGLayout.addWidget(self.totalCountLabel, 1, 0)
        self.statsGLayout.addWidget(self.statsMiddleVDivider, 1, 1)
        self.statsGLayout.addWidget(self.totalCountValueLabel, 1, 2)

        self.statsGLayout.addWidget(self.hommaCountLabel, 2, 0)
        self.statsGLayout.addWidget(self.statsBottomVDivider, 2, 1)
        self.statsGLayout.addWidget(self.hommaCountValueLabel, 2, 2)

        # Tab components for searchTabWidget
        self.memberTab = QWidget(self)
        self.tagTab = QWidget(self)
        self.dateTab = QWidget(self)
        self.hommaTab = QWidget(self)
        self.miscTab = QWidget(self)

        # Tab settings for searchTabWidget
        self.searchTabWidget.addTab(self.memberTab, "멤버")
        self.searchTabWidget.setTabText(0, "멤버")
        self.searchTabWidget.addTab(self.tagTab, "태그")
        self.searchTabWidget.setTabText(1, "태그")
        self.searchTabWidget.addTab(self.dateTab, "날짜")
        self.searchTabWidget.setTabText(2, "날짜")
        self.searchTabWidget.addTab(self.hommaTab, "홈마")
        self.searchTabWidget.setTabText(3, "홈마")
        self.searchTabWidget.addTab(self.miscTab, "기타")
        self.searchTabWidget.setTabText(4, "기타")

        # Components for memberTab
        self.memberHLayout = QHBoxLayout()
        self.memberSelectGLayout = QGridLayout()
        self.memberLogicVLayout = QVBoxLayout()
        self.memberTab.setLayout(self.memberHLayout)

        # Layout settings for memberTab
        self.memberHLayout.addStretch(1)
        self.memberHLayout.addLayout(self.memberSelectGLayout)
        self.memberHLayout.addStretch(1)
        self.memberHLayout.addLayout(self.memberLogicVLayout)
        self.memberHLayout.addStretch(1)

        # Components for memberSelectGLayout
        self.lilySelectButton = QPushButton("릴리", self)
        self.lilySelectButton.setCheckable(True)
        self.haewonSelectButton = QPushButton("해원", self)
        self.haewonSelectButton.setCheckable(True)
        self.sullyoonSelectButton = QPushButton("설윤", self)
        self.sullyoonSelectButton.setCheckable(True)
        self.baeSelectButton = QPushButton("배이", self)
        self.baeSelectButton.setCheckable(True)
        self.jiwooSelectButton = QPushButton("지우", self)
        self.jiwooSelectButton.setCheckable(True)
        self.kyujinSelectButton = QPushButton("규진", self)
        self.kyujinSelectButton.setCheckable(True)
        self.memberAllSelectButton = QPushButton("모두 선택", self)
        self.memberAllSelectButton.released.connect(self.memberSelectAllReact)
        self.memberAllDeselectButton = QPushButton("모두 제외", self)
        self.memberAllDeselectButton.released.connect(self.memberDeselectAllReact)

        # Layout settings for memberSelectGLayout
        self.memberSelectGLayout.setRowStretch(0, 1)
        self.memberSelectGLayout.addWidget(self.lilySelectButton, 1, 0)
        self.memberSelectGLayout.addWidget(self.haewonSelectButton, 1, 1)
        self.memberSelectGLayout.addWidget(self.sullyoonSelectButton, 2, 0)
        self.memberSelectGLayout.addWidget(self.baeSelectButton, 2, 1)
        self.memberSelectGLayout.addWidget(self.jiwooSelectButton, 3, 0)
        self.memberSelectGLayout.addWidget(self.kyujinSelectButton, 3, 1)
        self.memberSelectGLayout.addWidget(self.memberAllSelectButton, 4, 0)
        self.memberSelectGLayout.addWidget(self.memberAllDeselectButton, 4, 1)
        self.memberSelectGLayout.setRowStretch(5, 1)

        # Components for memberLogicVLayout
        self.memberLogicLabel = QLabel("검색 포함 조건", self)
        self.memberLogicLabel.setAlignment(Qt.AlignCenter)

        self.memberLogicHDivider = QFrame(self)
        self.memberLogicHDivider.setFrameShape(QFrame.HLine)
        self.memberLogicHDivider.setFrameShadow(QFrame.Sunken)

        self.memberLogicSuperset = QRadioButton("이 멤버는 포함", self)
        self.memberLogicSuperset.setChecked(True)
        self.memberLogicExact = QRadioButton("정확히 이 멤버", self)
        self.memberLogicOr = QRadioButton("적어도 한 멤버", self)

        # Layout settings for memberLogicVLayout
        self.memberLogicVLayout.addStretch(1)
        self.memberLogicVLayout.addWidget(self.memberLogicLabel)
        self.memberLogicVLayout.addWidget(self.memberLogicHDivider)
        self.memberLogicVLayout.addWidget(self.memberLogicExact)
        self.memberLogicVLayout.addWidget(self.memberLogicSuperset)
        self.memberLogicVLayout.addWidget(self.memberLogicOr)
        self.memberLogicVLayout.addStretch(1)

        # Components for tagTab
        self.tagTabHLayout = QHBoxLayout()
        self.tagSearchVLayout = QVBoxLayout()
        self.tagLogicVLayout = QVBoxLayout()
        self.tagTab.setLayout(self.tagTabHLayout)

        # Layout settings for tagTabHLayout
        self.tagTabHLayout.addStretch(1)
        self.tagTabHLayout.addLayout(self.tagSearchVLayout)
        self.tagTabHLayout.addStretch(1)
        self.tagTabHLayout.addLayout(self.tagLogicVLayout)
        self.tagTabHLayout.addStretch(1)

        # Components for tagSearchVLayout
        self.tagSearchLabel = QLabel("태그 검색", self)
        self.tagSearchLabel.setAlignment(Qt.AlignCenter)

        self.tagSearchComboBox = QComboBox(self)
        self.tagConditionManipHLayout = QHBoxLayout()

        self.tagSearchHDivider = QFrame(self)
        self.tagSearchHDivider.setFrameShape(QFrame.HLine)
        self.tagSearchHDivider.setFrameShadow(QFrame.Sunken)

        self.tagConditionDisplayLabel = QLabel(self)

        # Layout settings for tagSearchVLayout
        self.tagSearchVLayout.addStretch(1)
        self.tagSearchVLayout.addWidget(self.tagSearchLabel)
        self.tagSearchVLayout.addWidget(self.tagSearchComboBox)
        self.tagSearchVLayout.addLayout(self.tagConditionManipHLayout)
        self.tagSearchVLayout.addWidget(self.tagSearchHDivider)
        self.tagSearchVLayout.addWidget(self.tagConditionDisplayLabel)
        self.tagSearchVLayout.addStretch(1)

        # Componenets for tagConditionManipHLayout
        self.tagConditionAppendButton = QPushButton("태그 추가", self)
        self.tagConditionAppendButton.released.connect(self.appendTagReact)
        self.tagConditionResetButton = QPushButton("태그 초기화", self)
        self.tagConditionResetButton.released.connect(self.resetTagReact)

        # Layout settings for tagConditionManipHLayout
        self.tagConditionManipHLayout.addWidget(self.tagConditionAppendButton)
        self.tagConditionManipHLayout.addWidget(self.tagConditionResetButton)

        # Components for tagLogicVLayout
        self.tagLogicLabel = QLabel("검색 포함 조건", self)
        self.tagLogicLabel.setAlignment(Qt.AlignCenter)

        self.tagLogicHDivider = QFrame(self)
        self.tagLogicHDivider.setFrameShape(QFrame.HLine)
        self.tagLogicHDivider.setFrameShadow(QFrame.Sunken)

        self.tagLogicSuperset = QRadioButton("이 태그는 포함", self)
        self.tagLogicSuperset.setChecked(True)
        self.tagLogicExact = QRadioButton("정확히 이 태그", self)
        self.tagLogicOr = QRadioButton("적어도 한 태그", self)

        # Layout settings for tagLogicVLayout
        self.tagLogicVLayout.addStretch(1)
        self.tagLogicVLayout.addWidget(self.tagLogicLabel)
        self.tagLogicVLayout.addWidget(self.tagLogicHDivider)
        self.tagLogicVLayout.addWidget(self.tagLogicSuperset)
        self.tagLogicVLayout.addWidget(self.tagLogicExact)
        self.tagLogicVLayout.addWidget(self.tagLogicOr)
        self.tagLogicVLayout.addStretch(1)

        # Components for dateTab
        self.dateTabGLayout = QGridLayout()
        self.dateTab.setLayout(self.dateTabGLayout)

        # Components for dateTabGLayout
        self.dateTabLabel = QLabel("사진이 찍힌 날짜의 범위", self)
        self.dateStartTool = QDateEdit(self)
        self.dateStartTool.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.dateStartTool.setCalendarPopup(True)
        self.dateStartTool.setEnabled(False)
        self.dateEndTool = QDateEdit(self)
        self.dateEndTool.setCalendarPopup(True)
        self.dateEndTool.setEnabled(False)

        self.dateTabHDivider = QFrame(self)
        self.dateTabHDivider.setFrameShape(QFrame.HLine)
        self.dateTabHDivider.setFrameShadow(QFrame.Sunken)

        self.dateStartCheckbox = QCheckBox("이 날부터", self)
        self.dateStartCheckbox.clicked.connect(self.dateStartReact)
        self.dateEndCheckbox = QCheckBox("이 날까지", self)
        self.dateEndCheckbox.clicked.connect(self.dateEndReact)

        # Layout settings for dateTabGLayout
        self.dateTabGLayout.setRowStretch(0, 1)
        self.dateTabGLayout.addWidget(self.dateTabLabel, 1, 2)
        self.dateTabGLayout.addWidget(self.dateTabHDivider, 2, 2)
        self.dateTabGLayout.addWidget(self.dateStartTool, 3, 0)
        self.dateTabGLayout.addWidget(self.dateStartCheckbox, 3, 2)
        self.dateTabGLayout.addWidget(self.dateEndTool, 4, 0)
        self.dateTabGLayout.addWidget(self.dateEndCheckbox, 4, 2)
        self.dateTabGLayout.setRowStretch(5, 1)

        # Components for hommaTab
        self.hommaTabHLayout = QHBoxLayout()
        self.hommaSearchVLayout = QVBoxLayout()
        self.hommaLogicVLayout = QVBoxLayout()
        self.hommaTab.setLayout(self.hommaTabHLayout)

        # Layout settings for hommaTabHLayout
        self.hommaTabHLayout.addStretch(1)
        self.hommaTabHLayout.addLayout(self.hommaSearchVLayout)
        self.hommaTabHLayout.addStretch(1)
        self.hommaTabHLayout.addLayout(self.hommaLogicVLayout)
        self.hommaTabHLayout.addStretch(1)

        # Components for hommaSearchVLayout
        self.hommaSearchLabel = QLabel("전체 홈마 검색", self)
        self.hommaSearchLabel.setAlignment(Qt.AlignCenter)

        self.hommaSearchComboBox = QComboBox(self)
        self.hommaConditionManipHLayout = QHBoxLayout()

        self.hommaSearchHDivider = QFrame(self)
        self.hommaSearchHDivider.setFrameShape(QFrame.HLine)
        self.hommaSearchHDivider.setFrameShadow(QFrame.Sunken)

        self.hommaConditionDisplayLabel = QLabel(self)

        # Layout settings for hommaSearchVLayout
        self.hommaSearchVLayout.addStretch(1)
        self.hommaSearchVLayout.addWidget(self.hommaSearchLabel)
        self.hommaSearchVLayout.addWidget(self.hommaSearchComboBox)
        self.hommaSearchVLayout.addLayout(self.hommaConditionManipHLayout)
        self.hommaSearchVLayout.addWidget(self.hommaSearchHDivider)
        self.hommaSearchVLayout.addWidget(self.hommaConditionDisplayLabel)
        self.hommaSearchVLayout.addStretch(1)

        # Componenets for hommaConditionManipHLayout
        self.hommaConditionAppendButton = QPushButton("홈마 추가", self)
        self.hommaConditionAppendButton.released.connect(self.appendHommaReact)
        self.hommaConditionResetButton = QPushButton("홈마 초기화", self)
        self.hommaConditionResetButton.released.connect(self.resetHommaReact)

        # Layout settings for hommaConditionManipHLayout
        self.hommaConditionManipHLayout.addWidget(self.hommaConditionAppendButton)
        self.hommaConditionManipHLayout.addWidget(self.hommaConditionResetButton)

        # Components for hommaLogicVLayout
        self.hommaLogicLabel = QLabel("검색 포함 조건", self)
        self.hommaLogicLabel.setAlignment(Qt.AlignCenter)

        self.hommaLogicHDivider = QFrame(self)
        self.hommaLogicHDivider.setFrameShape(QFrame.HLine)
        self.hommaLogicHDivider.setFrameShadow(QFrame.Sunken)

        self.hommaLogicSuperset = QRadioButton("이 홈마도 포함", self)
        self.hommaLogicSuperset.setChecked(True)
        self.hommaLogicExact = QRadioButton("이 홈마만 포함", self)
        self.hommaLogicExcept = QRadioButton("이 홈마는 제외", self)

        # Layout settings for hommaLogicVLayout
        self.hommaLogicVLayout.addStretch(1)
        self.hommaLogicVLayout.addWidget(self.hommaLogicLabel)
        self.hommaLogicVLayout.addWidget(self.hommaLogicHDivider)
        self.hommaLogicVLayout.addWidget(self.hommaLogicSuperset)
        self.hommaLogicVLayout.addWidget(self.hommaLogicExact)
        self.hommaLogicVLayout.addWidget(self.hommaLogicExcept)
        self.hommaLogicVLayout.addStretch(1)

        # Components for miscTab
        self.miscTabVLayout = QVBoxLayout()
        self.miscTab.setLayout(self.miscTabVLayout)

        # Components for miscTabVLayout
        self.includeBanHommaCheckBox = QCheckBox("금지 홈마 포함", self)
        self.includeBubbleCheckBox = QCheckBox("버블 포함", self)

        # Layout settings for miscTabVLayout
        self.miscTabVLayout.addStretch(1)
        self.miscTabVLayout.addWidget(self.includeBanHommaCheckBox)
        self.miscTabVLayout.addWidget(self.includeBubbleCheckBox)
        self.miscTabVLayout.addStretch(1)

    # noinspection PyAttributeOutsideInit
    def initBar(self):
        # Menubar
        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)

        # PhotoBar
        self.photoMenu = self.menubar.addMenu('사진')

        self.addLocalPhotoAction = QAction('컴퓨터에서 사진 찾기', self)
        self.photoMenu.addAction(self.addLocalPhotoAction)
        self.addLocalPhotoAction.triggered.connect(self.localAdd)

        self.addTweetPhotoAction = QAction('X(트위터)에서 사진 찾기', self)
        self.photoMenu.addAction(self.addTweetPhotoAction)
        self.addTweetPhotoAction.triggered.connect(self.twitterAdd)

        self.photoMenu.addSeparator()

        self.searchSimilarPhotoAction = QAction('유사한 사진 찾기', self)
        self.photoMenu.addAction(self.searchSimilarPhotoAction)
        self.searchSimilarPhotoAction.triggered.connect(self.searchSimilarPhotos)

        self.seeAllPhotoAction = QAction('모든 사진 보기', self)
        self.photoMenu.addAction(self.seeAllPhotoAction)
        self.seeAllPhotoAction.triggered.connect(self.seeAllPhotos)

        # TestBar
        self.testMenu = self.menubar.addMenu('검사')

        self.singleBubbleTestAction = QAction('클립보드 사진 버블 검사', self)
        self.testMenu.addAction(self.singleBubbleTestAction)
        self.singleBubbleTestAction.triggered.connect(self.clipboardBubbleTest)

        self.setBubbleFolder = QAction('버블 폴더 설정', self)
        self.testMenu.addAction(self.setBubbleFolder)
        self.setBubbleFolder.triggered.connect(self.setBubbleFolderReact)

        self.testMenu.addSeparator()

        self.singleBanHommaTestAction = QAction('클립보드 사진 금홈 검사', self)
        self.testMenu.addAction(self.singleBanHommaTestAction)
        self.singleBanHommaTestAction.triggered.connect(self.clipboardBanHommaTest)

        # HommaBar
        self.hommaMenu = self.menubar.addMenu('홈마')

        self.editBanHommaAction = QAction('금지 홈마 편집', self)
        self.hommaMenu.addAction(self.editBanHommaAction)
        self.editBanHommaAction.triggered.connect(self.editBanHomma)

        # HelpBar
        self.helpMenu = self.menubar.addMenu('도움말')

    # noinspection PyAttributeOutsideInit
    def initLogic(self):
        self.tagCondition = []
        self.hommaCondition = []
        self.fetchGodokStats()
        self.updateTagComboBox()
        self.updateHommaComboBox()
        self.updateTagConditionDisplay()
        self.updateHommaConditionDisplay()

    def setBubbleFolderReact(self):
        if fname := QFileDialog.getExistingDirectory(self, "버블 폴더 설정"):
            self.godok.bubble_directory = fname

        self.godok.export()
        self.fetchGodokStats()

    def editBanHomma(self):
        editBanHomma = GodokAssistant.EditBanHomma(self.godok)
        editBanHomma.setGeometry(500, 500, 500, 500)
        editBanHomma.exec_()

        self.fetchGodokStats()
        self.godok.export()

    def seeAllPhotos(self):
        paths, metas = [], []
        for __path, __meta in self.godok.data.items():
            paths.append(__path)
            metas.append(__meta['meta'])

        self.viewDetailDialog(paths, metas, '')

    def searchSimilarPhotos(self):
        similarityDialog = GodokAssistant.SimilarityDialog(self)
        similarityDialog.setGeometry(500, 500, 500, 500)
        similarityDialog.exec_()

    def clipboardBubbleTest(self):
        if len(self.godok.bubble_directory) == 0:
            QMessageBox.critical(self, "버블 폴더 설정되지 않음", "먼저 버블 사진이 담긴 하나의 폴더를 선택해주세요.",
                                 QMessageBox.Ok)
            return

        similarityDialog = GodokAssistant.SimilarityDialog(self)
        similarityDialog.bubbleOnlyRadio.setChecked(True)
        similarityDialog.importFromClipboardReact()
        similarityDialog.setGeometry(500, 500, 500, 500)
        similarityDialog.exec_()

    def clipboardBanHommaTest(self):
        similarityDialog = GodokAssistant.SimilarityDialog(self)
        similarityDialog.hommaOnlyRadio.setChecked(True)
        similarityDialog.importFromClipboardReact()
        similarityDialog.setGeometry(500, 500, 500, 500)
        similarityDialog.exec_()

    def localAdd(self):
        fname = QFileDialog.getOpenFileNames(self, '컴퓨터에서 사진 불러오기', filter="이미지 (*.png *.jpg *.bmp *.jpeg)")
        if not fname[0]: return
        self.viewDetailDialog(fname[0],
                              [{'source': '',
                                'members': 0,
                                'homma': '(알 수 없음)',
                                'date': (datetime.today().year, datetime.today().month, datetime.today().day),
                                'tags': [''] * 6,
                                'dir': os.path.split(path)[0]} for path in fname[0]],
                              '')

    def twitterAdd(self):
        # Check for internet connection
        if not self.godok.test_internet_connectivity():
            QMessageBox.critical(self, "인터넷 연결 안됨", "[X(트위터)에서 가져오기] 기능을 사용하려면 "
                                                    "인터넷에 연결되어 있어야 합니다.", QMessageBox.Close)
            return

        scrapeDialog = GodokAssistant.ScrapeDialog(self)
        scrapeDialog.setGeometry(500, 500, 500, 500)
        scrapeDialog.exec_()

    def fetchGodokStats(self):
        tot, permit, hommas = self.godok.stats()
        self.totalCountValueLabel.setText(str(tot))
        self.sharableCountValueLabel.setText(str(permit))
        self.hommaCountValueLabel.setText(str(hommas))

    def updateTagComboBox(self):
        self.tagSearchComboBox.clear()
        self.tagSearchComboBox.addItems(self.godok.tags)

    def updateHommaComboBox(self):
        self.hommaSearchComboBox.clear()
        self.hommaSearchComboBox.addItems(self.godok.hommas)

    def viewDetailDialog(self, loadDirList: list[str], metadata: list[dict], desc: str):
        detailDialog = GodokAssistant.DetailDialog(loadDirList, metadata, desc, self.godok)
        detailDialog.setGeometry(500, 500, 500, 500)
        detailDialog.exec_()

        self.fetchGodokStats()
        self.updateTagComboBox()
        self.updateHommaComboBox()

    def memberSelectAllReact(self):
        self.lilySelectButton.setChecked(True)
        self.haewonSelectButton.setChecked(True)
        self.sullyoonSelectButton.setChecked(True)
        self.baeSelectButton.setChecked(True)
        self.jiwooSelectButton.setChecked(True)
        self.kyujinSelectButton.setChecked(True)

    def memberDeselectAllReact(self):
        self.lilySelectButton.setChecked(False)
        self.haewonSelectButton.setChecked(False)
        self.sullyoonSelectButton.setChecked(False)
        self.baeSelectButton.setChecked(False)
        self.jiwooSelectButton.setChecked(False)
        self.kyujinSelectButton.setChecked(False)

    def dateStartReact(self):
        self.dateStartTool.setEnabled(self.dateStartCheckbox.isChecked())

    def dateEndReact(self):
        self.dateEndTool.setEnabled(self.dateEndCheckbox.isChecked())

    def appendTagReact(self):
        if self.tagSearchComboBox.currentText() not in self.tagCondition:
            self.tagCondition.append(self.tagSearchComboBox.currentText())
            self.updateTagConditionDisplay()

    def resetTagReact(self):
        self.tagCondition = []
        self.updateTagConditionDisplay()

    def updateTagConditionDisplay(self):
        r = ''
        for __tag in self.tagCondition:
            r += f'{__tag}, '

        if len(r) == 0:
            self.tagConditionDisplayLabel.setText('(태그 조건 없음)')
        else:
            self.tagConditionDisplayLabel.setText(r[:-2])

    def appendHommaReact(self):
        if self.hommaSearchComboBox.currentText() not in self.hommaCondition:
            self.hommaCondition.append(self.hommaSearchComboBox.currentText())
            self.updateHommaConditionDisplay()

    def resetHommaReact(self):
        self.hommaCondition = []
        self.updateHommaConditionDisplay()

    def updateHommaConditionDisplay(self):
        r = ''
        for __homma in self.hommaCondition:
            r += f'{__homma}, '

        if len(r) == 0:
            self.hommaConditionDisplayLabel.setText('(홈마 조건 없음)')
        else:
            self.hommaConditionDisplayLabel.setText(r[:-2])

    def resetSettings(self):
        self.initUI()
        self.initLogic()

    def initSearch(self):
        __search_cond = {'members': {'bitval': self.lilySelectButton.isChecked() * 32
                                               + self.haewonSelectButton.isChecked() * 16
                                               + self.sullyoonSelectButton.isChecked() * 8
                                               + self.baeSelectButton.isChecked() * 4
                                               + self.jiwooSelectButton.isChecked() * 2
                                               + self.kyujinSelectButton.isChecked(),
                                     'logic': 'superset' if self.memberLogicSuperset.isChecked()
                                     else 'strict' if self.memberLogicExact.isChecked()
                                     else 'atleast'},
                         'tags': {'tests': self.tagCondition,
                                  'logic': 'superset' if self.tagLogicSuperset.isChecked()
                                  else 'strict' if self.tagLogicExact.isChecked()
                                  else 'atleast'},
                         'date': {'start': (self.dateStartTool.date().year(),
                                            self.dateStartTool.date().month(),
                                            self.dateStartTool.date().day()),
                                  'end': (self.dateEndTool.date().year(),
                                          self.dateEndTool.date().month(),
                                          self.dateEndTool.date().day()),
                                  'startlogic': self.dateStartCheckbox.isChecked(),
                                  'endlogic': self.dateEndCheckbox.isChecked()},
                         'homma': {'tests': self.hommaCondition,
                                   'logic': 'superset' if self.hommaLogicSuperset.isChecked()
                                   else 'strict' if self.hommaLogicExcept.isChecked()
                                   else 'except'},
                         'misc': {'banHommaInclude': self.includeBanHommaCheckBox.isChecked(),
                                  'bubbleInclude': self.includeBubbleCheckBox.isChecked()}
                         }

        __paths, __metas = self.godok.search(__search_cond)
        if len(__paths) == 0:
            QMessageBox.information(self, "검색 일치 결과 없음", "주어진 조건을 모두 만족하는 사진을 찾지 못했습니다.", QMessageBox.Ok)
            return

        self.viewDetailDialog(__paths, __metas, '')

    @staticmethod
    def pillow_from_clipboard() -> Image.Image | None:
        clipboard = QApplication.clipboard()
        qt_image = clipboard.image()

        if qt_image.isNull():
            return None

        buffer = qt_image.bits().asstring(qt_image.byteCount())
        pil_image = Image.frombytes(
            "RGBA",
            (qt_image.width(), qt_image.height()),
            buffer,
            "raw",
            "BGRA"
        )
        return pil_image

    @staticmethod
    def copy_image_to_clipboard(image_path: str):
        """Copy a PIL.Image to the clipboard as a QImage."""
        global qimage

        pil_image = Image.open(image_path)
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")

        data = pil_image.tobytes("raw", "RGBA")
        w, h = pil_image.size
        qimage = QImage(data, w, h, QImage.Format_RGBA8888)

        clipboard = QApplication.clipboard()
        clipboard.setImage(qimage)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GodokAssistant()
    sys.exit(app.exec_())
