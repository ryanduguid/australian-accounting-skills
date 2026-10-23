// CPython 3.14.8 codec registry and single-byte mappings; see PYTHON-LICENSE.txt.
pub fn canonical(name: &str) -> Option<&'static str> {
    Some(match name {
        "646" | "ansi_x3.4_1968" | "ansi_x3.4_1986" | "ansi_x3_4_1968" | "ascii" | "cp367"
        | "csascii" | "ibm367" | "iso646_us" | "iso_646.irv_1991" | "iso_ir_6" | "us"
        | "us_ascii" => "ascii",
        "base64" | "base64_codec" | "base_64" => "base64",
        "big5" | "big5_tw" | "csbig5" | "x_mac_trad_chinese" => "big5",
        "big5_hkscs" | "big5hkscs" | "hkscs" => "big5hkscs",
        "bz2" | "bz2_codec" => "bz2",
        "charmap" => "charmap",
        "037" | "cp037" | "csibm037" | "ebcdic_cp_ca" | "ebcdic_cp_nl" | "ebcdic_cp_us"
        | "ebcdic_cp_wt" | "ibm037" | "ibm039" => "cp037",
        "cp1006" => "cp1006",
        "1026" | "cp1026" | "csibm1026" | "ibm1026" => "cp1026",
        "1125" | "cp1125" | "cp866u" | "ibm1125" | "ruscii" => "cp1125",
        "1140" | "cp01140" | "cp1140" | "csibm01140" | "ebcdic_us_37_euro" | "ibm01140"
        | "ibm1140" => "cp1140",
        "1250" | "cp1250" | "windows_1250" => "cp1250",
        "1251" | "cp1251" | "windows_1251" => "cp1251",
        "1252" | "cp1252" | "windows_1252" => "cp1252",
        "1253" | "cp1253" | "windows_1253" => "cp1253",
        "1254" | "cp1254" | "windows_1254" => "cp1254",
        "1255" | "cp1255" | "windows_1255" => "cp1255",
        "1256" | "cp1256" | "windows_1256" => "cp1256",
        "1257" | "cp1257" | "windows_1257" => "cp1257",
        "1258" | "cp1258" | "windows_1258" => "cp1258",
        "273" | "cp273" | "csibm273" | "ibm273" => "cp273",
        "424" | "cp424" | "csibm424" | "ebcdic_cp_he" | "ibm424" => "cp424",
        "437" | "cp437" | "cspc8codepage437" | "ibm437" => "cp437",
        "500" | "cp500" | "csibm500" | "ebcdic_cp_be" | "ebcdic_cp_ch" | "ibm500" => "cp500",
        "cp720" => "cp720",
        "cp737" => "cp737",
        "775" | "cp775" | "cspc775baltic" | "ibm775" => "cp775",
        "850" | "cp850" | "cspc850multilingual" | "ibm850" => "cp850",
        "852" | "cp852" | "cspcp852" | "ibm852" => "cp852",
        "855" | "cp855" | "csibm855" | "ibm855" => "cp855",
        "cp856" => "cp856",
        "857" | "cp857" | "csibm857" | "ibm857" => "cp857",
        "858"
        | "cp00858"
        | "cp858"
        | "csibm00858"
        | "csibm858"
        | "ibm00858"
        | "ibm858"
        | "pc_multilingual_850_euro" => "cp858",
        "860" | "cp860" | "csibm860" | "ibm860" => "cp860",
        "861" | "cp861" | "cp_is" | "csibm861" | "ibm861" => "cp861",
        "862" | "cp862" | "cspc862latinhebrew" | "ibm862" => "cp862",
        "863" | "cp863" | "csibm863" | "ibm863" => "cp863",
        "864" | "cp864" | "csibm864" | "ibm864" => "cp864",
        "865" | "cp865" | "csibm865" | "ibm865" => "cp865",
        "866" | "cp866" | "csibm866" | "ibm866" => "cp866",
        "869" | "cp869" | "cp_gr" | "csibm869" | "ibm869" => "cp869",
        "874" | "cp874" | "ms874" | "windows_874" => "cp874",
        "cp875" => "cp875",
        "932" | "cp932" | "ms932" | "ms_kanji" | "mskanji" | "windows_31j" => "cp932",
        "949" | "cp949" | "ms949" | "uhc" => "cp949",
        "950" | "cp950" | "ms950" => "cp950",
        "euc_jis2004" | "euc_jis_2004" | "eucjis2004" | "jisx0213" => "euc_jis_2004",
        "euc_jisx0213" | "eucjisx0213" => "euc_jisx0213",
        "euc_jp" | "eucjp" | "u_jis" | "ujis" => "euc_jp",
        "cseuckr" | "euc_kr" | "euckr" | "korean" | "ks_c_5601" | "ks_c_5601_1987"
        | "ks_x_1001" | "ksc5601" | "ksx1001" | "x_mac_korean" => "euc_kr",
        "gb18030" | "gb18030_2000" => "gb18030",
        "chinese" | "csiso58gb231280" | "euc_cn" | "euccn" | "eucgb2312_cn" | "gb2312"
        | "gb2312_1980" | "gb2312_80" | "iso_ir_58" | "x_mac_simp_chinese" => "gb2312",
        "936" | "cp936" | "gbk" | "ms936" => "gbk",
        "hex" | "hex_codec" => "hex",
        "cp1051" | "hp_roman8" | "ibm1051" | "r8" | "roman8" => "hp-roman8",
        "hz" | "hz_gb" | "hz_gb_2312" | "hzgb" => "hz",
        "idna" => "idna",
        "csiso2022jp" | "iso2022_jp" | "iso2022jp" | "iso_2022_jp" => "iso2022_jp",
        "iso2022_jp_1" | "iso2022jp_1" | "iso_2022_jp_1" => "iso2022_jp_1",
        "iso2022_jp_2" | "iso2022jp_2" | "iso_2022_jp_2" => "iso2022_jp_2",
        "iso2022_jp_2004" | "iso2022jp_2004" | "iso_2022_jp_2004" => "iso2022_jp_2004",
        "iso2022_jp_3" | "iso2022jp_3" | "iso_2022_jp_3" => "iso2022_jp_3",
        "iso2022_jp_ext" | "iso2022jp_ext" | "iso_2022_jp_ext" => "iso2022_jp_ext",
        "csiso2022kr" | "iso2022_kr" | "iso2022kr" | "iso_2022_kr" => "iso2022_kr",
        "8859" | "cp819" | "csisolatin1" | "ibm819" | "iso8859" | "iso8859_1" | "iso_8859_1"
        | "iso_8859_1_1987" | "iso_ir_100" | "l1" | "latin" | "latin1" | "latin_1" => "iso8859-1",
        "csisolatin6" | "iso8859_10" | "iso_8859_10" | "iso_8859_10_1992" | "iso_ir_157" | "l6"
        | "latin6" => "iso8859-10",
        "iso8859_11" | "iso_8859_11" | "iso_8859_11_2001" | "thai" => "iso8859-11",
        "iso8859_13" | "iso_8859_13" | "l7" | "latin7" => "iso8859-13",
        "iso8859_14" | "iso_8859_14" | "iso_8859_14_1998" | "iso_celtic" | "iso_ir_199" | "l8"
        | "latin8" => "iso8859-14",
        "iso8859_15" | "iso_8859_15" | "l9" | "latin9" => "iso8859-15",
        "iso8859_16" | "iso_8859_16" | "iso_8859_16_2001" | "iso_ir_226" | "l10" | "latin10" => {
            "iso8859-16"
        }
        "csisolatin2" | "iso8859_2" | "iso_8859_2" | "iso_8859_2_1987" | "iso_ir_101" | "l2"
        | "latin2" => "iso8859-2",
        "csisolatin3" | "iso8859_3" | "iso_8859_3" | "iso_8859_3_1988" | "iso_ir_109" | "l3"
        | "latin3" => "iso8859-3",
        "csisolatin4" | "iso8859_4" | "iso_8859_4" | "iso_8859_4_1988" | "iso_ir_110" | "l4"
        | "latin4" => "iso8859-4",
        "csisolatincyrillic" | "cyrillic" | "iso8859_5" | "iso_8859_5" | "iso_8859_5_1988"
        | "iso_ir_144" => "iso8859-5",
        "arabic" | "asmo_708" | "csisolatinarabic" | "ecma_114" | "iso8859_6" | "iso_8859_6"
        | "iso_8859_6_1987" | "iso_ir_127" => "iso8859-6",
        "csisolatingreek" | "ecma_118" | "elot_928" | "greek" | "greek8" | "iso8859_7"
        | "iso_8859_7" | "iso_8859_7_1987" | "iso_ir_126" => "iso8859-7",
        "csisolatinhebrew" | "hebrew" | "iso8859_8" | "iso_8859_8" | "iso_8859_8_1988"
        | "iso_8859_8_e" | "iso_8859_8_i" | "iso_ir_138" => "iso8859-8",
        "csisolatin5" | "iso8859_9" | "iso_8859_9" | "iso_8859_9_1989" | "iso_ir_148" | "l5"
        | "latin5" => "iso8859-9",
        "cp1361" | "johab" | "ms1361" => "johab",
        "cskoi8r" | "koi8_r" => "koi8-r",
        "koi8_t" => "koi8-t",
        "koi8_u" => "koi8-u",
        "kz1048" | "kz_1048" | "rk1048" | "strk1048_2002" => "kz1048",
        "mac_arabic" => "mac-arabic",
        "mac_croatian" => "mac-croatian",
        "mac_cyrillic" | "maccyrillic" => "mac-cyrillic",
        "mac_farsi" => "mac-farsi",
        "mac_greek" | "macgreek" => "mac-greek",
        "mac_iceland" | "maciceland" => "mac-iceland",
        "mac_centeuro" | "mac_latin2" | "maccentraleurope" | "maclatin2" => "mac-latin2",
        "mac_roman" | "macintosh" | "macroman" => "mac-roman",
        "mac_romanian" => "mac-romanian",
        "mac_turkish" | "macturkish" => "mac-turkish",
        "ansi" | "dbcs" | "mbcs" => "mbcs",
        "oem" => "oem",
        "palmos" => "palmos",
        "cp154" | "csptcp154" | "cyrillic_asian" | "pt154" | "ptcp154" => "ptcp154",
        "punycode" => "punycode",
        "quopri" | "quopri_codec" | "quoted_printable" | "quotedprintable" => "quopri",
        "raw_unicode_escape" => "raw-unicode-escape",
        "rot13" | "rot_13" => "rot-13",
        "csshiftjis" | "s_jis" | "shift_jis" | "shiftjis" | "sjis" | "x_mac_japanese" => {
            "shift_jis"
        }
        "s_jis_2004" | "shift_jis_2004" | "shiftjis2004" | "sjis_2004" => "shift_jis_2004",
        "s_jisx0213" | "shift_jisx0213" | "shiftjisx0213" | "sjisx0213" => "shift_jisx0213",
        "iso_ir_166" | "tis620" | "tis_620" | "tis_620_0" | "tis_620_2529_0" | "tis_620_2529_1" => {
            "tis-620"
        }
        "undefined" => "undefined",
        "unicode_escape" => "unicode-escape",
        "u16" | "utf16" | "utf_16" => "utf-16",
        "unicodebigunmarked" | "utf_16_be" | "utf_16be" => "utf-16-be",
        "unicodelittleunmarked" | "utf_16_le" | "utf_16le" => "utf-16-le",
        "u32" | "utf32" | "utf_32" => "utf-32",
        "utf_32_be" | "utf_32be" => "utf-32-be",
        "utf_32_le" | "utf_32le" => "utf-32-le",
        "u7" | "unicode_1_1_utf_7" | "utf7" | "utf_7" => "utf-7",
        "cp65001" | "u8" | "utf" | "utf8" | "utf8_ucs2" | "utf8_ucs4" | "utf_8" => "utf-8",
        "utf_8_sig" => "utf-8-sig",
        "uu" | "uu_codec" => "uu",
        "zip" | "zlib" | "zlib_codec" => "zlib",
        _ => return None,
    })
}
pub fn is_text(name: &str) -> bool {
    !matches!(
        name,
        "base64" | "bz2" | "hex" | "quopri" | "rot-13" | "uu" | "zlib"
    )
}
pub fn single_byte(name: &str) -> Option<&'static [u8]> {
    static DATA: &[u8] = include_bytes!("source_single_byte.bin");
    let offset = match name {
        "cp037" => 0,
        "cp1006" => 1024,
        "cp1026" => 2048,
        "cp1125" => 3072,
        "cp1140" => 4096,
        "cp1250" => 5120,
        "cp1251" => 6144,
        "cp1252" => 7168,
        "cp1253" => 8192,
        "cp1254" => 9216,
        "cp1255" => 10240,
        "cp1256" => 11264,
        "cp1257" => 12288,
        "cp1258" => 13312,
        "cp273" => 14336,
        "cp424" => 15360,
        "cp437" => 16384,
        "cp500" => 17408,
        "cp720" => 18432,
        "cp737" => 19456,
        "cp775" => 20480,
        "cp850" => 21504,
        "cp852" => 22528,
        "cp855" => 23552,
        "cp856" => 24576,
        "cp857" => 25600,
        "cp858" => 26624,
        "cp860" => 27648,
        "cp861" => 28672,
        "cp862" => 29696,
        "cp863" => 30720,
        "cp864" => 31744,
        "cp865" => 32768,
        "cp866" => 33792,
        "cp869" => 34816,
        "cp874" => 35840,
        "cp875" => 36864,
        "hp-roman8" => 37888,
        "iso8859-1" => 38912,
        "iso8859-10" => 39936,
        "iso8859-11" => 40960,
        "iso8859-13" => 41984,
        "iso8859-14" => 43008,
        "iso8859-15" => 44032,
        "iso8859-16" => 45056,
        "iso8859-2" => 46080,
        "iso8859-3" => 47104,
        "iso8859-4" => 48128,
        "iso8859-5" => 49152,
        "iso8859-6" => 50176,
        "iso8859-7" => 51200,
        "iso8859-8" => 52224,
        "iso8859-9" => 53248,
        "koi8-r" => 54272,
        "koi8-t" => 55296,
        "koi8-u" => 56320,
        "kz1048" => 57344,
        "mac-arabic" => 58368,
        "mac-croatian" => 59392,
        "mac-cyrillic" => 60416,
        "mac-farsi" => 61440,
        "mac-greek" => 62464,
        "mac-iceland" => 63488,
        "mac-latin2" => 64512,
        "mac-roman" => 65536,
        "mac-romanian" => 66560,
        "mac-turkish" => 67584,
        "palmos" => 68608,
        "ptcp154" => 69632,
        "tis-620" => 70656,
        _ => return None,
    };
    Some(&DATA[offset..offset + 1024])
}
