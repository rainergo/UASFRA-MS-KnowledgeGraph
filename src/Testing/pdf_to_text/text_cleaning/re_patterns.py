import re
from typing import Pattern

""" BRACKETS """
RE_BRACKETS_CURLY_AND_CONTENT: Pattern = re.compile(r"\{[^{}]*?\}")
RE_BRACKETS_ROUND_AND_CONTENT: Pattern = re.compile(r"\([^()]*?\)")
RE_BRACKETS_SQUARE_AND_CONTENT: Pattern = re.compile(r"\[[^\[\]]*?\]")
RE_BRACKETS_CURLY: Pattern = re.compile(r"[{}]")
RE_BRACKETS_ROUND: Pattern = re.compile(r"[()]")
RE_BRACKETS_SQUARE: Pattern = re.compile(r"[\[\]]")

""" LINEBREAKS, SPACES """
RE_LINEBREAK: Pattern = re.compile(r"(\r\n|[\n\v])+")
# RE_NO_PERIOD_NOR_HYPHEN_THEN_TWO_EMPTY_LINES: Pattern = re.compile(r"(?<![.-])(?:\r\n|[\n\v]){2,}")
RE_NONBREAKING_SPACE: Pattern = re.compile(r"[^\S\n\v]+")
RE_ZERO_WIIDTH_SPACE: Pattern = re.compile(r"[\u200B\u2060\uFEFF]+")
RE_SPACE_BEFORE_SENT_END: Pattern = re.compile(r"\s+(?=\.)")

RE_HEADLINE: Pattern = re.compile(r"(?P<headline>\A\b(?:.|\n){,200}?$)(?=\n{2,})",
                                  flags=re.MULTILINE)
RE_SECTION_HEADER: Pattern = re.compile(r"(?<!\A)(?<=\n{2})(?P<sectionheader>^\b[^.!?]*?$)(?=\n{2,})",
                                        flags=re.MULTILINE)

""" LISTINGS """
num_of_required_hyphens = 2
hyphen_chars = '-*o'  # The chars therein must be present in function: RE_BULLET_POINTS.sub(repl="*", string=text)
RE_LISTING_SENTS: Pattern = re.compile(
    fr"(?P<listing>(?:(?P<beforechar>\W)\W*)(?P<hyphen>(?<=\n)[^\S\r\n]*[{hyphen_chars}]\s+)[^.!?]+?(?P<afterchar>[.!?]?)(?=(?<=\n)[^\S\r\n][{hyphen_chars}]\s+|\s*\n+^\W|(?<=\.)))"
    , flags=re.MULTILINE)


RE_LISTING_SENTS: Pattern = re.compile(
    fr"(?P<listing>(?:(?P<beforechar>\W)\W*)(?P<hyphen>(?<=\n)[^\S\r\n]*[{hyphen_chars}]\s+)[^.!?]+?(?P<afterchar>[.!?]?)(?=(?<=\n)[^\S\r\n][{hyphen_chars}]\s+|\s*\n+^\W|(?<=\.)))"
    , flags=re.MULTILINE)



""" DATES AND TIMES """
RE_DATE_1_DAY_MONTHNAME_YEAR: Pattern = re.compile(
    r"\b(?P<day1>[0-3]?[0-9])[.\s/-]*(?P<monthname1>(?:jan|feb|m[aä]r|apr|ma[iy][^\w]|jun|jul|aug|sep|o[ck]t|nov|de[cz])\w*)(?:[,.\s/-]*(?P<year1>[1|2]?[0|9]?[0-9]{2})?)",
    flags=re.IGNORECASE)
RE_DATE_2_MONTHNAME_DAY_YEAR: Pattern = re.compile(
    r"\b(?P<monthname2>(?:jan|feb|m[aä]r|apr|ma[iy][^\w]|jun|jul|aug|sep|o[ck]t|nov|de[cz])\w*)\s*(?P<day2>[0-3]?[0-9]),?\s+(?P<year2>[1|2]?[0|9]?[0-9]{2})?",
    flags=re.IGNORECASE)
RE_DATE_3_DAY_MONTHNUMBER_YEAR: Pattern = re.compile(
    r"\b(?P<day3>[0-3]?[0-9])[\s/.-]+(?P<monthnum3>[0-1][0-9])[\s/.-]+(?P<year3>(?:[1|2][0|9])?[0-9]{2})",
    flags=re.IGNORECASE)
RE_DATE_4_YEAR_MONTHNUMBER_DAY: Pattern = re.compile(
    r"\b(?P<year4>(?:[1|2][0|9])?[0-9]{2})[-/.\s]+(?P<monthnum4>[0-1]?[0-9])[-/.\s]+(?P<day4>[0-3]?[0-9])",
    flags=re.IGNORECASE)
RE_DATE_EXACT: Pattern = re.compile('(?P<date>' + '|'.join(
    [RE_DATE_1_DAY_MONTHNAME_YEAR.pattern, RE_DATE_2_MONTHNAME_DAY_YEAR.pattern, RE_DATE_3_DAY_MONTHNUMBER_YEAR.pattern,
     RE_DATE_4_YEAR_MONTHNUMBER_DAY.pattern]) + ')',
                                    flags=re.IGNORECASE)
RE_TIME: Pattern = re.compile(
    r"(?P<time>(?P<hour>[0-2]?[0-9]):(?P<min>[0-5][0-9]):?(?P<sec>[0-5][0-9])?\s*(?P<pm>p\.?m\.?)?\s*(?P<am>a\.?m\.?)?\s*(?:(?P<gmtoffset>(?:GMT|UTC)(?P<offset>[+-]\d\d?))|(?P<tzname>(?:CET)|(?:EET)|(?:GMT[^\w+-])|(?:UTC[^\w+-])|(?:UCT[^\w+-])|(?:EST)|(?:WET)|(?:MET)|(?:HST)|(?:MST)))?(?P<timesuffix>(?:/CEST))?)",
    flags=re.IGNORECASE)

RE_DATE_AND_TIME = re.compile(RE_DATE_EXACT.pattern + r"[\s/-]*" + RE_TIME.pattern + r"\b", flags=re.IGNORECASE)
RE_YEAR_PERIOD = re.compile(r"([1|2][9|0]\d{2}\.)")
RE_MONTH_YEAR: Pattern = re.compile(
    r"\b(?:(?P<day1>[0-3]?[0-9])(?:[\.\s\/\-,]*))?(?P<month>(?:jan|feb|m[aä]r|apr|ma[iy]|jun|jul|aug|sep|o[ck]t|nov|de[cz])\w*)\s*(?:(?P<day2>[0-3]?[0-9])(?:[\.\s\/\-,]*))?(?P<year>(?:[1|2][0|9])[0-9]{2})\b",
    flags=re.IGNORECASE)

start_and_end_chars: str = "-+#"
RE_LOCATION_DATE_TIMEOPTIONAL: Pattern = re.compile(
    r"^"
    + r"(?P<locationbeforedate>(?:[A-Z])[^\n\d]{1,50}(?P<dateprefix>[,-]|den|der|am)\s*)" + r"?"  # Optional. Include location, then time-related sent starts
    + RE_DATE_EXACT.pattern
    + r"[\s/-]*?"
    + RE_TIME.pattern + r"?"  # Optional
    + fr"(?P<endchars>(?:([{start_and_end_chars}][^\S\n\r]*)+(?=.*))|$)"
    , flags=re.MULTILINE | re.IGNORECASE | re.VERBOSE
)

RE_DATE_TIME_ONLY_LINES: Pattern = re.compile(
    r"^"
    + fr"(?P<startchars>(?:[^\S\n\r\w]|[{start_and_end_chars}])*)" + r"?"    #Optional
    + RE_DATE_EXACT.pattern
    + r"[\s/-]*?"
    + RE_TIME.pattern + r"?"    # Optional
    + fr"(?P<endcharsnowords>(?:[^\S\n\r\w]|[{start_and_end_chars}])*(?!\w))" + r"?"
    + r"$"
    , flags=re.MULTILINE | re.IGNORECASE | re.VERBOSE
)


""" CHARS """
RE_SUSPICIOUS_CHARS: Pattern = re.compile(r"[\\#<>+|~^°=►¬]+")
RE_UNICODE_SYMBOLS: Pattern = re.compile(r"([\u00ab\u00BB\u00AE\u2310\u2500])")
RE_STRANGE_DASHES: Pattern = re.compile(r"([\u2010-\u2015\uFF0D\uFE63\u2043\u1680\u002D\u2043\u1806\u2212])")
RE_SUPER_SUB_SCRIPTED_NUMBERS: Pattern = re.compile(r"([\u2070\u00B9\u00B2\u00B3\u2074\u2075\u2076\u2077\u2078\u2079\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089])")
RE_BULLET_POINTS: Pattern = re.compile(
    # require bullet points as first non-whitespace char on a new line, like a list to catch it later in listing
    r"((^|\n)\s*?)"
    r"([\u2022\u2023\u2043\u204C\u204D\u2219\u25aa\u25CF\u25E6\u29BE\u29BF\u30fb\u25BA])",
)

repeat_chars: str = "-.?,"
RE_REPEATING_CHARS: Pattern = re.compile(
    fr"(?:(?P<spacebefore>\s*)*(?P<repeatchar>[{repeat_chars}])(?P<spaceafter>\s*)){{2,}}")

RE_CURR_SYMBOL: Pattern = re.compile(r"[$¢£¤¥ƒ֏؋৲৳૱௹฿៛ℳ元円圆圓﷼\u20A0-\u20C0]")
RE_CURR_AMOUNT: Pattern = re.compile(r"(?P<curr>EUR|USD|GBP|JPY)(?:\s{0,})(?P<amount>[\,\.\d]+)(?P<unit>\s*\w{1,}\.?)",
                                     flags=re.IGNORECASE)

RE_MEASUREMENTS: Pattern = re.compile(r"(?P<amount>\d+)\s*(?P<unit>(?:mm|cm|m|km|km2)(?:2|3)?)",
                                      flags=re.IGNORECASE)

RE_MEASUREMENTS_PERIOD: Pattern = re.compile(r"(?P<unit>(?:mm|cm|m|km)(?:2|3)?)\.",
                                             flags=re.IGNORECASE)
# Quotation marks
RE_QUOTATION_MARKS: Pattern = re.compile(r"\'(?!s)|\"")

""" EMOJIS """
RE_EMOJI: Pattern = re.compile(
    r"[\u2600-\u26FF\u2700-\u27BF\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U0001FA70-\U0001FAFF]",
    flags=re.IGNORECASE,
)

""" INTERNET, EMAIL, PHONE """
RE_URL: Pattern = re.compile(
    r"(?:^|(?<![\w/.]))"
    # protocol identifier
    # r"(?:(?:https?|ftp)://)"  <-- alt?
    r"(?:(?:https?://|ftp://|www\d{0,3}\.))"
    # user:pass authentication
    r"(?:\S+(?::\S*)?@)?"
    r"(?:"
    # IP address exclusion
    # private & local networks
    r"(?!(?:10|127)(?:\.\d{1,3}){3})"
    r"(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})"
    r"(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
    # IP address dotted notation octets
    # excludes loopback network 0.0.0.0
    # excludes reserved space >= 224.0.0.0
    # excludes network & broadcast addresses
    # (first & last IP address of each class)
    r"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
    r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
    r"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
    r"|"
    # host name
    r"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9])"
    # domain name
    r"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9])*"
    # TLD identifier
    r"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
    r")"
    # port number
    r"(?::\d{2,5})?"
    # resource path
    r"(?:/\S*)?"
    r"(?:$|(?![\w?!+&/]))",
    flags=re.IGNORECASE,
)

RE_SHORT_URL: Pattern = re.compile(
    r"(?:^|(?<![\w/.]))"
    # optional scheme
    r"(?:(?:https?://)?)"
    # domain
    r"(?:\w-?)*?\w+(?:\.[a-z]{2,12}){1,3}"
    r"/"
    # hash
    r"[^\s.,?!'\"|+]{2,12}"
    r"(?:$|(?![\w?!+&/]))",
    flags=re.IGNORECASE,
)

RE_URL_DOMAIN: Pattern = re.compile(
    r"(?P<https>\bhttps?://)?(?P<www>(?:www|\w+)\.)?(?P<domain>(?:\w|-)+)(?P<ending>\.(?:com|de|net|org|io|co|us|uk|au|edu|int|gov|ai|biz)/?)",
    flags=re.IGNORECASE)

RE_HTTP_LINKS: Pattern = re.compile(
    r"(?P<beforelinks>(?:Link|Bildlink|Quellen)[^:]*:\s*)" + r"?"  # Optional
    + RE_URL.pattern
    , flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE)

RE_EMAIL: Pattern = re.compile(
    r"(?:mailto:)?"
    r"(?:^|(?<=[^\w@.)]))([\w+-](\.(?!\.))?)*?[\w+-]@(?:\w-?)*?\w+(\.([a-z]{2,})){1,3}"
    r"(?:$|(?=\b))",
    flags=re.IGNORECASE,
)

RE_PHONE_NUMBER: Pattern = re.compile("(%s|%s)" % (
    # Intl.
    r"(?:\+(?:1|44|90)[\-\s]+[0-9]{3}([\-\s0-9]{4,11}(?:$|\s)))|(?:\+[0-9]{2,3}[\-\s]+\(?[0-9]{2,5}\)?[\/\-\s0-9]{4,11}(?:$|\s))",
    # National
    r"(?P<nat1>0|\+)?(?(nat1)[0-9]{2,5}|\(0?[0-9]{2,5}\))[\s\-\/]([\-\s\d]{3,11})($|\s+)"),
                                      flags=re.IGNORECASE)

""" Abbreviations: """
RE_ABBREVIATION: Pattern = re.compile(r"(?<!-)\b[a-zA-Z]{1,7}\.\-{0,1}(?:[a-zA-Z]{1,4}\.){0,2}", flags=re.IGNORECASE)

""" EXTRA """
RE_UPPERCASE_WORS: Pattern = re.compile(r"\b[A-ZÄÖÜ]+\b")


if __name__ == '__main__':
    print(RE_BULLET_POINTS.pattern)