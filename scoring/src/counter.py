from dialogue import Dialogue


class Counter:
    def __init__(self, txt_file_path: str, start_yyyymmdd: int = None, end_yyyymmdd: int = None):
        self.merge: list[Dialogue] = []
        self.by_date: dict[str, list[Dialogue]] = {}
        self.by_speaker: dict[str, list[Dialogue]] = {}

        __in_select = start_yyyymmdd is None
        __start_rich = f'{start_yyyymmdd // 10000}년 {(start_yyyymmdd % 10000) // 100}월 {start_yyyymmdd % 100}일' \
            if start_yyyymmdd is not None else 'S_None'
        __end_rich = f'{end_yyyymmdd // 10000}년 {(end_yyyymmdd % 10000) // 100}월 {end_yyyymmdd % 100}일' \
            if end_yyyymmdd is not None else 'E_None'
        __date = "Unknown!@#$%^&*"

        with open(txt_file_path, 'r', encoding='utf-8') as f:
            for dialogue_chunk in f.read().replace('--------------- ', '[[Date divider ').split('\n['):
                if dialogue_chunk.find('Date divider ') != -1:
                    # Found date indicator: update date
                    __temp = Dialogue('[' + dialogue_chunk)
                    __date = __temp.date_info
                    if __date.find(__start_rich) != -1: __in_select = True
                    if __date.find(__end_rich) != -1: __in_select = False

                # Get a chunk of a potential dialogue
                if __in_select: self.merge.append(Dialogue('[' + dialogue_chunk))

        # Assign date and sort
        current_date: str = 'Unknown!@#$%^&*'
        for dialogue in self.merge:
            if dialogue.date_info.startswith("Unknown"): dialogue.date_info = current_date
            else: current_date = dialogue.date_info

            # Sort by date
            if current_date not in self.by_date.keys(): self.by_date[current_date] = []
            self.by_date[current_date].append(dialogue)

            # Sort by speaker
            if dialogue.speaker not in self.by_speaker.keys(): self.by_speaker[dialogue.speaker] = []
            self.by_speaker[dialogue.speaker].append(dialogue)

    def assign_birthtime_scores(self) -> dict[str, dict[str, int]]:
        __BIRTHTIME_ORDER = ['오전 솔시', '오전 설시', '오전 행시', '오전 쮸시', '오전 뀨시', '오전 릴시',
                             '오후 솔시', '오후 설시', '오후 행시', '오후 쮸시', '오후 뀨시', '오후 릴시']
        __BIRTHTIME_TABLE = {'오전 솔시': ((0, 28), {'솔', '배이', '이모티콘', '뵤', '뱅', '소올', 'sol'}),
                             '오전 설시': ((1, 26), {'설', '설윤', '이모티콘', '윤아', '서얼', 'sul'}),
                             '오전 행시': ((2, 25), {'행', '해원', '이모티콘', '농담', '담곰', 'haewon', 'hae'}),
                             '오전 쮸시': ((4, 13), {'쮸', '지우', '이모티콘', '댕', 'woo'}),
                             '오전 뀨시': ((5, 26), {'뀨', '규진', '이모티콘', '냥', 'kyu'}),
                             '오전 릴시': ((10, 17), {'릴', '릴리', '이모티콘', '댕', 'lil'}),
                             '오후 솔시': ((12, 28), {'솔', '배이', '이모티콘', '뵤', '뱅', '소올', 'sol'}),
                             '오후 설시': ((13, 26), {'설', '설윤', '이모티콘', '윤아', '서얼', 'sul'}),
                             '오후 행시': ((14, 25), {'행', '해원', '이모티콘', '농담', '담곰', 'haewon', 'hae'}),
                             '오후 쮸시': ((16, 13), {'쮸', '지우', '이모티콘', '댕', 'woo'}),
                             '오후 뀨시': ((17, 26), {'뀨', '규진', '이모티콘', '냥', 'kyu'}),
                             '오후 릴시': ((22, 17), {'릴', '릴리', '이모티콘', '댕', 'lil'})}

        assignment: dict[str, dict[str, int]] = {}

        for date, dialogues in self.by_date.items():
            current_time_whole = 0
            __tdesc = __BIRTHTIME_ORDER[0]
            __twhole = Dialogue.hm_to_whole(__BIRTHTIME_TABLE[__tdesc][0])
            __success_temp = []

            for dialogue in dialogues + [None]:
                if dialogue is None: current_time_whole += 1
                else: current_time_whole = dialogue.time_whole

                # When a birthtime passes, assign scores
                if current_time_whole > __twhole:
                    if len(__success_temp) != 0:
                        # Assign first birthtime success (+2)
                        __birthtime_asg = {k: (1 if __twhole < 720 else 0) for k in __success_temp}
                        __birthtime_asg[__success_temp[0]] += 2
                        __birthtime_asg[__success_temp[-1]] += 2
                        if len(__success_temp) >= 3: __birthtime_asg[__success_temp[2]] += 1
                        assignment[f'{date} {__tdesc}'] = __birthtime_asg

                    # Rotate birthtime agendas until a valid target (1338: One minute after Lily PM)
                    __BIRTHTIME_ORDER.append(__BIRTHTIME_ORDER.pop(0))
                    __tdesc = __BIRTHTIME_ORDER[0]
                    __twhole = Dialogue.hm_to_whole(__BIRTHTIME_TABLE[__tdesc][0])
                    while __twhole < current_time_whole < 1338:
                        __BIRTHTIME_ORDER.append(__BIRTHTIME_ORDER.pop(0))
                        __tdesc = __BIRTHTIME_ORDER[0]
                        __twhole = Dialogue.hm_to_whole(__BIRTHTIME_TABLE[__tdesc][0])

                    __success_temp.clear()

                # Check for birthtime success
                if __twhole == current_time_whole:
                    if dialogue.birthtime_challenge(*__BIRTHTIME_TABLE[__tdesc]):
                        __success_temp.append(dialogue.speaker)

        return assignment

    def assign_communication_scores(self) -> dict[str, int]:
        assignment: dict[str, int] = {s: (len(d) // 22) * 2 for s, d in self.by_speaker.items()
                                      if not s.startswith("Server")}
        return assignment

    def assign_photo_link_scores(self) -> dict[str, int]:
        count: dict[str, int] = {s: 0 for s in self.by_speaker.keys()}
        for speaker, dialogs in self.by_speaker.items():
            for dialog in dialogs:
                count[speaker] += dialog.get_photo_count()
                count[speaker] += len(dialog.get_link_domain())

        return {s: (5 if count[s] >= 60 else 0) for s in self.by_speaker.keys() if not s.startswith("Server")}

    def score_total(self) -> dict[str, int]:
        total = {s: 0 for s in self.by_speaker.keys()}
        for birthtime in self.assign_birthtime_scores().values():
            for speaker, score in birthtime.items():
                total[speaker] += score

        for speaker, score in self.assign_communication_scores().items(): total[speaker] += score
        for speaker, score in self.assign_photo_link_scores().items(): total[speaker] += score

        return total


if __name__ == '__main__':
    c = Counter('../dat/KakaoTalk_20250707_0127_01_304_group.txt', 20250707, 20250708)
    for k, v in c.assign_birthtime_scores().items():
        print(f'{k}: {v}')
