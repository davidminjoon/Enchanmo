import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QFrame, \
    QTabWidget, QLabel, QScrollArea, QPushButton, QRadioButton, QComboBox, QDateEdit, QCheckBox, QSizePolicy, QAction, \
    QDialog, QLineEdit
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class GodokAssistant(QMainWindow):
    def __init__(self):
        super().__init__()

        # Visual aspects
        QApplication.setFont(QFont("SUITE", 10))

        # Highest hierarchy object
        self.bigHLayout = QHBoxLayout()
        self.scaffoldCentralWidget = QWidget(self)
        self.scaffoldCentralWidget.setLayout(self.bigHLayout)
        self.setCentralWidget(self.scaffoldCentralWidget)

        # Components for bigHLayout
        self.searchSettingVLayout = QVBoxLayout()

        self.bigVDivider = QFrame(self)
        self.bigVDivider.setFrameShape(QFrame.VLine)
        self.bigVDivider.setFrameShadow(QFrame.Sunken)

        self.searchResultsVLayout = QVBoxLayout()

        # Layout settings for bigHLayout
        self.bigHLayout.addLayout(self.searchSettingVLayout)
        self.bigHLayout.addWidget(self.bigVDivider)
        self.bigHLayout.addLayout(self.searchResultsVLayout)

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

        # Components for searchResultsVLayout
        self.searchResultsLabel = QLabel("사진 검색 결과",  self)
        self.searchResultsScroll = QScrollArea(self)

        self.searchResultsHDivider = QFrame(self)
        self.searchResultsHDivider.setFrameShape(QFrame.HLine)
        self.searchResultsHDivider.setFrameShadow(QFrame.Sunken)

        self.searchResultsManipHLayout = QHBoxLayout()

        # Layout settings for searchResultsVLayout
        self.searchResultsVLayout.addWidget(self.searchResultsLabel)
        self.searchResultsVLayout.addWidget(self.searchResultsScroll)
        self.searchResultsVLayout.addWidget(self.searchResultsHDivider)
        self.searchResultsVLayout.addLayout(self.searchResultsManipHLayout)

        # Components for searchInitHLayout
        self.searchSettingResetButton = QPushButton("검색 조건 초기화", self)
        self.searchInitButton = QPushButton("검색 시작", self)

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
        self.sulyoonSelectButton = QPushButton("설윤", self)
        self.sulyoonSelectButton.setCheckable(True)
        self.baeSelectButton = QPushButton("배이", self)
        self.baeSelectButton.setCheckable(True)
        self.jiwooSelectButton = QPushButton("지우", self)
        self.jiwooSelectButton.setCheckable(True)
        self.kyujinSelectButton = QPushButton("규진", self)
        self.kyujinSelectButton.setCheckable(True)
        self.memberAllSelectButton = QPushButton("모두 선택", self)
        self.memberAllDeselectButton = QPushButton("모두 제외", self)

        # Layout settings for memberSelectGLayout
        self.memberSelectGLayout.setRowStretch(0, 1)
        self.memberSelectGLayout.addWidget(self.lilySelectButton, 1, 0)
        self.memberSelectGLayout.addWidget(self.haewonSelectButton, 1, 1)
        self.memberSelectGLayout.addWidget(self.sulyoonSelectButton, 2, 0)
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

        self.memberLogicExact = QRadioButton("정확히 이 멤버", self)
        self.memberLogicExact.setChecked(True)
        self.memberLogicSuperset = QRadioButton("이 멤버는 포함", self)
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
        self.tagConditionResetButton = QPushButton("태그 초기화", self)

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
        self.dateEndCheckbox = QCheckBox("이 날까지", self)

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
        self.hommaConditionResetButton = QPushButton("홈마 초기화", self)

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

        # Components for searchResultsManipHLayout
        self.searchResultsSelectAllButton = QPushButton("모두 선택", self)
        self.searchResultsDeselectAllButton = QPushButton("모두 제외", self)
        self.searchResultsExportButton = QPushButton("내보내기", self)

        # Layout settings for searchResultsManipHLayout
        self.searchResultsManipHLayout.addWidget(self.searchResultsSelectAllButton)
        self.searchResultsManipHLayout.addWidget(self.searchResultsDeselectAllButton)
        self.searchResultsManipHLayout.addWidget(self.searchResultsExportButton)

        # Menubar
        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)

        # PhotoBar
        self.photoMenu = self.menubar.addMenu('사진')

        self.addLocalPhotoAction = QAction('컴퓨터에서 사진 찾기', self)
        self.photoMenu.addAction(self.addLocalPhotoAction)

        self.addTweetPhotoAction = QAction('X(트위터)에서 사진 찾기', self)
        self.photoMenu.addAction(self.addTweetPhotoAction)

        self.photoMenu.addSeparator()

        self.setBubbleFolder = QAction('버블 폴더 설정', self)
        self.photoMenu.addAction(self.setBubbleFolder)

        # TestBar
        self.testMenu = self.menubar.addMenu('검사')

        self.singleBubbleTestAction = QAction('클립보드 사진 버블 검사', self)
        self.testMenu.addAction(self.singleBubbleTestAction)

        self.multipleBubbleTestAction = QAction('여러 사진 버블 검사', self)
        self.testMenu.addAction(self.multipleBubbleTestAction)

        self.testMenu.addSeparator()

        self.singleBanHommaTestAction = QAction('클립보드 사진 금홈 검사', self)
        self.testMenu.addAction(self.singleBanHommaTestAction)

        self.multipleBanHommaTestAction = QAction('여러 사진 금홈 검사', self)
        self.testMenu.addAction(self.multipleBanHommaTestAction)

        # HommaBar
        self.hommaMenu = self.menubar.addMenu('홈마')

        self.addBanHommaAction = QAction('금지 홈마 추가', self)
        self.hommaMenu.addAction(self.addBanHommaAction)

        self.editBanHommaAction = QAction('금지 홈마 편집', self)
        self.hommaMenu.addAction(self.editBanHommaAction)

        # Geometry
        self.setWindowTitle("고독방 도우미")
        self.setGeometry(100, 100, 636, 480)
        self.show()

    def viewDetailDialog(self):
        class DetailDialog(QDialog):
            def __init__(self):
                super().__init__()

                # Highest object hierarchy
                self.bigHLayout = QHBoxLayout()
                self.setLayout(self.bigHLayout)

                # Components for bigHLayout
                self.imageViewVLayout = QVBoxLayout()
                self.infoEditGLayout = QGridLayout()

                # Layout settings for bigHLayout
                self.bigHLayout.addLayout(self.imageViewVLayout)
                self.bigHLayout.addLayout(self.infoEditGLayout)

                # Components for imageViewVLayout
                self.imageDisplayLabel = QLabel(self)
                self.imageMoveHLayout = QHBoxLayout()

                # Layout settings for imageViewVLayout
                self.imageViewVLayout.addWidget(self.imageDisplayLabel)
                self.imageViewVLayout.addStretch(1)
                self.imageViewVLayout.addLayout(self.imageMoveHLayout)

                # Components for imageMoveHLayout
                self.leftButton = QPushButton("<", self)
                self.leftButton.setMaximumWidth(30)
                self.currentLabel = QLabel(self)
                self.rightButton = QPushButton(">", self)
                self.rightButton.setMaximumWidth(30)

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
                self.memberButtonGLayout = QGridLayout()
                self.hommaSettingHLayout = QHBoxLayout()
                self.shootDateEdit = QDateEdit(self)
                self.tagGLayout = QGridLayout()
                self.originalDirectoryHLayout = QHBoxLayout()
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
                self.infoEditGLayout.addLayout(self.originalDirectoryHLayout, 5, 1)
                self.infoEditGLayout.setROwStretch(6, 1)
                self.infoEditGLayout.addLayout(self.miscSettingGLayout, 7, 1)

                # Components for memberButtonGLayout
                self.lilyButton = QPushButton("릴리", self)
                self.haewonButton = QPushButton("해원", self)
                self.sulyoonButton = QPushButton("설윤", self)
                self.baeButton = QPushButton("배이", self)
                self.jiwooButton = QPushButton("지우", self)
                self.kyujinButton = QPushButton("규진", self)

                # Layout settings for memberButtonGLayout
                self.memberButtonGLayout.addWidget(self.lilyButton, 0, 0)
                self.memberButtonGLayout.addWidget(self.haewonButton, 0, 1)
                self.memberButtonGLayout.addWidget(self.sulyoonButton, 0, 2)
                self.memberButtonGLayout.addWidget(self.baeButton, 1, 0)
                self.memberButtonGLayout.addWidget(self.jiwooButton, 1, 1)
                self.memberButtonGLayout.addWidget(self.kyujinButton, 1, 2)

                # Components for hommaSettingHLayout
                self.hommaManualEdit = QLineEdit(self)
                self.hommaSelectComboBox = QComboBox(self)

                # Layout settings for hommaSettingHLayout
                self.hommaSettingHLayout.addWidget(self.hommaManualEdit)
                self.hommaSettingHLayout.addWidget(self.hommaSelectComboBox)

                # Components for tagGLayout
                self.tagManualEditList = [QLineEdit(self) for _ in range(6)]

                # Layout settings for tagGLayout
                for i in range(6):
                    self.tagGLayout.addWidget(self.tagManualEditList[i], *divmod(i, 2))

                # Components for miscSettingGLayout
                self.makeCopyCheckbox = QCheckBox("사본 저장하기", self)
                self.copyToAllCheckbox = QCheckBox("모든 사진에 동일한 내용 적용", self)
                self.completeButton = QPushButton("완료하기", self)

                # Layout settings for miscSettingGLayout
                self.miscSettingGLayout.addWidget(self.makeCopyCheckbox, 0, 0)
                self.miscSettingGLayout.addWidget(self.copyToAllCheckbox, 1, 0)
                self.miscSettingGLayout.addWidget(self.completeButton, 1, 1)

        detailDialog = DetailDialog()
        detailDialog.setGeometry(500, 500, 500, 500)
        detailDialog.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GodokAssistant()
    sys.exit(app.exec_())


