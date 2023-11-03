import re

from . import re_patterns as repat


class CleanText:
    # Tables
    TBL_UMLAUTE: dict = {'ä': 'ae', 'Ä': 'Ae', 'ö': 'oe', 'Ö': 'Oe', 'ü': 'ue', 'Ü': 'Ue', 'ß': 'ss'}
    TBL_ACCENTS: dict = {'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'å': 'a', 'À': 'A', 'Á': 'A', 'Â': 'A',
                         'ç': 'c',
                         'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 'ȩ': 'e', 'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
                         'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i', 'Î': 'I', 'Ï': 'I',
                         'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'Ô': 'O', 'Ò': 'O', 'Ó': 'O',
                         'ù': 'u', 'ú': 'u', 'û': 'u', 'Ù': 'U', 'Û': 'U'}
    TBL_CURRENCY: dict = {'€': 'EUR', '$': 'USD', '£': 'GBP', '¥': 'JPY'}
    TBL_FANCY_QUOTATION_MARKS: dict[int, int] = {
        ord(x): ord(y) for x, y in
        [("ʼ", "'"), ("‘", "'"), ("’", "'"), ("´", "'"), ("`", "'"), ("“", '"'), ("”", '"'), ("„", "'")]}

    # Substitutions: Replace special character with value in respective TBL
    def sub_umlaute(self, text: str) -> str:
        table = str.maketrans(self.TBL_UMLAUTE)
        return text.translate(table)

    def sub_accent_chars(self, text: str) -> str:
        table = str.maketrans(self.TBL_ACCENTS)
        return text.translate(table)

    def sub_currency(self, text: str) -> str:
        """ Function makes space between curr, amount and unit (i.e. EUR200M -> EUR 200 M) to improve tokenization """
        table = str.maketrans(self.TBL_CURRENCY)
        text = text.translate(table)
        return repat.RE_CURR_AMOUNT.sub(
            repl=lambda m: m.group("curr") + ' ' + m.group("amount") + ' ' + m.group("unit"),
            string=text)

    def sub_measurements(self, text: str) -> str:
        """ Function makes space between amount and unit (i.e. 200km -> 200 km) to improve tokenization """
        return repat.RE_MEASUREMENTS.sub(
            repl=lambda m: m.group("amount") + ' ' + m.group("unit"), string=text)

    def sub_fancy_quot_marks(self, text: str) -> str:
        table = str.maketrans(self.TBL_FANCY_QUOTATION_MARKS)
        return text.translate(table)

    def rem_quot_marks(self, text: str) -> str:
        return repat.RE_QUOTATION_MARKS.sub(repl="", string=text)

    def rem_brackets(self, text: str, curly: bool = True, round: bool = True, square: bool = True) -> str:
        text = repat.RE_BRACKETS_CURLY_AND_CONTENT.sub(repl="", string=text) if curly else text
        text = repat.RE_BRACKETS_ROUND_AND_CONTENT.sub(repl="", string=text) if round else text
        text = repat.RE_BRACKETS_SQUARE_AND_CONTENT.sub(repl="", string=text) if square else text
        return text

    def rem_strange_chars(self, text: str) -> str:
        text = repat.RE_SUPER_SUB_SCRIPTED_NUMBERS.sub(repl=" ", string=text)
        text = repat.RE_SUSPICIOUS_CHARS.sub(repl=" ", string=text)
        text = repat.RE_BULLET_POINTS.sub(repl="*", string=text)
        text = repat.RE_UNICODE_SYMBOLS.sub(repl="", string=text)
        text = repat.RE_STRANGE_DASHES.sub(repl="-", string=text)
        return text

    def rem_datetime_only_lines(self, text: str):
        text = repat.RE_LOCATION_DATE_TIMEOPTIONAL.sub(repl="", string=text)
        text = repat.RE_DATE_TIME_ONLY_LINES.sub(repl="", string=text)
        return text

    def rem_address_info(self, text: str):
        text = repat.RE_HTTP_LINKS.sub(repl="", string=text)
        text = repat.RE_EMAIL.sub(repl="", string=text)
        return text

    def mark_end_of_sentence(self, text: str, period: str = ". ") -> str:
        """ An end of sentence pattern can be manifold. Multiple patterns are thus (probably) required. """
        text = repat.RE_HEADLINE.sub(repl=lambda m: m.group("headline") + period, string=text)
        text = repat.RE_SECTION_HEADER.sub(repl=lambda m: m.group("sectionheader") + period, string=text)
        return text

    def split_listed_sentences(self, text: str, end_of_sent_char: str = ". ") -> str:
        possible_chars_to_mark_end_of_sents: list = [".", ":"]
        try:
            listing_objs: list[re.Match] = list(repat.RE_LISTING_SENTS.finditer(string=text))
            end_pos: int = 0
            for listing_obj in listing_objs:
                if listing_obj.start() == end_pos or listing_obj.group(
                        'beforechar') in possible_chars_to_mark_end_of_sents:
                    hyphen_replacement: str = ""
                else:
                    hyphen_replacement: str = end_of_sent_char
                if listing_obj.group('afterchar') in possible_chars_to_mark_end_of_sents:
                    char_added_at_end: str = ""
                else:
                    char_added_at_end: str = end_of_sent_char
                end_pos = listing_obj.end()
                cleaned_listing = listing_obj.group('listing').replace(listing_obj.group('hyphen'),
                                                                       hyphen_replacement) + char_added_at_end
                text = text.replace(listing_obj.group('listing'), cleaned_listing)

        except:
            # ToDo: Logger here
            pass
        return text

    def rem_repeating_chars(self, text: str):
        text = repat.RE_REPEATING_CHARS.sub(
            repl=lambda m: m.group(0)[0] + " ", string=text)
        return text

    def rem_uppercase_words(self, text: str) -> str:
        text = repat.RE_UPPERCASE_WORS.sub(repl="", string=text)
        return text

    def rem_whitespace(self, text: str) -> str:
        """
        Replace all contiguous zero-width and line-breaking spaces and spaces before a sentence end with an empty
        string, non-line-breaking spaces with a single space and then strip any leading/trailing whitespace.
        """
        text = repat.RE_ZERO_WIIDTH_SPACE.sub(repl="", string=text)
        text = repat.RE_LINEBREAK.sub(repl=r" ", string=text)
        text = repat.RE_NONBREAKING_SPACE.sub(repl=" ", string=text)
        text = repat.RE_SPACE_BEFORE_SENT_END.sub(repl="", string=text)
        return text.strip()

    def clean(self, text: str,
              sub_umlaute: bool = True, sub_accent_chars: bool = True, sub_curr: bool = True, sub_measure: bool = True,
              sub_fancy_quot_marks: bool = True, rem_brackets: bool = True, rem_quot_marks: bool = True,
              rem_strange_chars: bool = True, mark_end_of_sent: bool = True, split_listed_sents: bool = True,
              rem_dt_only_lines: bool = True, rem_address_info: bool = True, rem_uppercase_words: bool = True,
              rem_repeat_chars: bool = True, rem_whitespace: bool = True) -> str:

        # text = self.rem_uppercase_words(text=text) if rem_uppercase_words else text
        text = self.sub_umlaute(text=text) if sub_umlaute else text
        text = self.sub_accent_chars(text=text) if sub_accent_chars else text
        text = self.sub_currency(text=text) if sub_curr else text
        text = self.sub_measurements(text=text) if sub_measure else text
        text = self.sub_fancy_quot_marks(text=text) if sub_fancy_quot_marks else text
        text = self.rem_quot_marks(text=text) if rem_quot_marks else text  # Should be after sub_fancy_quot_marks !!!
        text = self.rem_strange_chars(text=text) if rem_strange_chars else text
        text = self.rem_datetime_only_lines(text=text) if rem_dt_only_lines else text
        text = self.rem_brackets(text=text) if rem_brackets else text
        text = self.rem_address_info(text=text) if rem_address_info else text
        text = self.mark_end_of_sentence(text=text) if mark_end_of_sent else text
        text = self.split_listed_sentences(text=text) if split_listed_sents else text
        text = self.rem_repeating_chars(text=text) if rem_repeat_chars else text  # rem_repeating_chars: do second last
        text = self.rem_whitespace(text=text) if rem_whitespace else text  # rem_whitespace: do last !!!
        return text