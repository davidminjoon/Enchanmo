from __future__ import annotations
from re import match


class Dialogue:
    def __init__(self, log_text: str):
        self.dialogue: str = ''
        self.speaker: str = "Server!@#$%^&*"
        self.time_text: str = "Server!@#$%^&*"
        self.date_info: str = 'Unknown!@#$%^&*'
        self.morning_text: bool = True
        self.time_hour, self.time_min, self.time_whole = 0, 0, 0
        self.time_hm = (0, 0)

        for line in log_text.split('\n'):
            # Sort out server-side messages
            if line.endswith('님이 들어왔습니다.'): continue
            if line.endswith('님이 나갔습니다.'): continue
            if line.endswith('님이 부방장이 되었습니다.'): continue
            if line.endswith('님이 부방장에서 해제되었습니다.'): continue
            if line.endswith('개의 메시지를 가렸습니다.'): continue

            # Preserve date info
            if line.startswith('[[Date divider ') and line.endswith('---------------'):
                self.date_info = line[15: -16]
                continue

            # If this line is the start of a dialogue, fetch dialogue time and speaker
            char_ptr = 0
            if line.startswith('['):
                # Fetch dialogue speaker
                char_ptr = line.find(']')
                if char_ptr == -1: continue
                self.speaker: str = line[1: char_ptr]

                # Fetch time text
                __ochar = char_ptr
                char_ptr = line.find(']', __ochar + 2)
                if char_ptr == -1: continue
                self.time_text: str = line[__ochar + 3: char_ptr]

                # Parse time text
                __colon_idx = self.time_text.index(':')
                __txth, __txtm = int(self.time_text[3: __colon_idx]) % 12, int(self.time_text[__colon_idx + 1:])
                self.morning_text: int = (self.time_text[1] == '전')
                self.time_hour: int = int(not self.morning_text) * 12 + __txth
                self.time_minute: int = __txtm
                self.time_hm: tuple[int, int] = (self.time_hour, self.time_minute)
                self.time_whole: int = self.time_hour * 60 + self.time_minute

                # Set character pointer to start of dialogue
                char_ptr += 2

            # Fetch dialogue
            self.dialogue += line[char_ptr:] + '\n'

        # Trim the final line break
        self.dialogue = self.dialogue[:-1]

    @staticmethod
    def hm_to_whole(time_hm: tuple[int, int]) -> int:
        return time_hm[0] * 60 + time_hm[1]

    @staticmethod
    def whole_to_hm(time_whole: int) -> tuple[int, int]:
        return divmod(time_whole, 60)

    def birthtime_challenge(self, birthtime_hm: tuple[int, int], test_chars: set[str]) -> bool:
        """
        Returns True if this dialogue was sent precisely at the time (``birthtime_hm[0]``: ``birthtime_hm[1]``)
        and contains at least one of the characters in ``test_chars``.
        :param birthtime_hm: A tuple of (hour, minute) to test for.
        :param test_chars: A set of single-letter characters to test for.
        :return: True if the birthtime challenge conditions are all satisfied. False otherwise.
        """
        # Check time constraint
        if self.hm_to_whole(birthtime_hm) != self.time_whole: return False

        # Check letter containment constraint
        for test_char in test_chars:
            if test_char in self.dialogue: return True
        return False

    def get_link_domain(self) -> list[str]:
        """
        If the dialogue contains links, returns their domains. (specified by "https://youtube.com/...")
        :return: If the dialogue contains links, a list of their domains. Empty list otherwise.
        """
        __ret_list: list[str] = []
        __domain_end = 0
        while __http_idx := self.dialogue.find('https://', __domain_end) + 8:
            if __http_idx == 7: return __ret_list
            __domain_end = self.dialogue.find('/', __http_idx)
            __ret_list.append(self.dialogue[__http_idx: __domain_end])

    def get_photo_count(self) -> int:
        """
        If the dialogue is a photo send, returns their count.
        :return: If the dialogue is a photo send, its count. 0 otherwise.
        """
        if not match(r'^사진( [0-9]{1,2}장)?$', self.dialogue): return 0
        if not self.dialogue.endswith('장'): return 1
        return int(self.dialogue[3: -1])

    def __eq__(self, other: Dialogue) -> bool:
        return __eq__(self.time_whole, other.time_whole)

    def __gt__(self, other: Dialogue) -> bool:
        return __gt__(self.time_whole, other.time_whole)

    def __str__(self):
        return f'[{self.speaker}] [{self.time_text}] {self.dialogue}'

    def __repr__(self):
        return self.__str__()

