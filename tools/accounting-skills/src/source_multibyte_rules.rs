// Generated from CPython 3.14.8 multibyte incremental decoders. See PYTHON-LICENSE.txt.
pub const LENGTH: usize = 2920686;
pub const OUTPUT_OFFSETS: usize = 2482628;
pub const OUTPUT_BYTES: usize = 2710976;
pub fn table(name: &str) -> Option<(usize, usize)> {
    Some(match name {
        "big5" => (8, 129),
        "big5hkscs" => (132620, 129),
        "cp932" => (265232, 61),
        "cp949" => (327940, 129),
        "cp950" => (460552, 129),
        "euc_jis_2004" => (593164, 385),
        "euc_jisx0213" => (988944, 385),
        "euc_jp" => (1384724, 385),
        "gb2312" => (1780504, 129),
        "gbk" => (1913116, 129),
        "hz" => (2045728, 131),
        "johab" => (2180396, 129),
        "shift_jis" => (2313008, 43),
        "shift_jis_2004" => (2357212, 61),
        "shift_jisx0213" => (2419920, 61),
        _ => return None,
    })
}
