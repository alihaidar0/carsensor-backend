FUEL_TYPE_MAP = {
    "ガソリン": "Gasoline",
    "ハイブリッド": "Hybrid",
    "電気": "Electric",
    "ディーゼル": "Diesel",
    "プラグインハイブリッド": "Plug-in Hybrid",
    "天然ガス": "Natural Gas",
    "その他": "Other",
}

TRANSMISSION_MAP = {
    "AT": "AT",
    "MT": "MT",
    "CVT": "CVT",
    "セミAT": "Semi-AT",
    "その他": "Other",
}

BODY_TYPE_MAP = {
    "セダン": "Sedan",
    "SUV・クロカン": "SUV",
    "ミニバン・バン": "Minivan",
    "軽自動車": "Kei Car",
    "コンパクト": "Compact",
    "ワゴン": "Wagon",
    "クーペ": "Coupe",
    "オープン": "Convertible",
    "ハッチバック": "Hatchback",
    "トラック・バス": "Truck/Bus",
    "その他": "Other",
}

DRIVE_TYPE_MAP = {
    "4WD": "4WD",
    "FF": "FF",
    "FR": "FR",
    "MR": "MR",
    "RR": "RR",
    "AWD": "AWD",
}

COLOR_MAP = {
    "ホワイト": "White",
    "ブラック": "Black",
    "シルバー": "Silver",
    "グレー": "Gray",
    "レッド": "Red",
    "ブルー": "Blue",
    "グリーン": "Green",
    "ブラウン": "Brown",
    "ゴールド": "Gold",
    "ベージュ": "Beige",
    "オレンジ": "Orange",
    "パープル": "Purple",
    "イエロー": "Yellow",
    "その他": "Other",
}

PREFECTURE_MAP = {
    "北海道": "Hokkaido",
    "青森": "Aomori",
    "岩手": "Iwate",
    "宮城": "Miyagi",
    "秋田": "Akita",
    "山形": "Yamagata",
    "福島": "Fukushima",
    "茨城": "Ibaraki",
    "栃木": "Tochigi",
    "群馬": "Gunma",
    "埼玉": "Saitama",
    "千葉": "Chiba",
    "東京": "Tokyo",
    "神奈川": "Kanagawa",
    "新潟": "Niigata",
    "富山": "Toyama",
    "石川": "Ishikawa",
    "福井": "Fukui",
    "山梨": "Yamanashi",
    "長野": "Nagano",
    "岐阜": "Gifu",
    "静岡": "Shizuoka",
    "愛知": "Aichi",
    "三重": "Mie",
    "滋賀": "Shiga",
    "京都": "Kyoto",
    "大阪": "Osaka",
    "兵庫": "Hyogo",
    "奈良": "Nara",
    "和歌山": "Wakayama",
    "鳥取": "Tottori",
    "島根": "Shimane",
    "岡山": "Okayama",
    "広島": "Hiroshima",
    "山口": "Yamaguchi",
    "徳島": "Tokushima",
    "香川": "Kagawa",
    "愛媛": "Ehime",
    "高知": "Kochi",
    "福岡": "Fukuoka",
    "佐賀": "Saga",
    "長崎": "Nagasaki",
    "熊本": "Kumamoto",
    "大分": "Oita",
    "宮崎": "Miyazaki",
    "鹿児島": "Kagoshima",
    "沖縄": "Okinawa",
}


def translate_fuel_type(value):
    return FUEL_TYPE_MAP.get(value, value)


def translate_transmission(value):
    return TRANSMISSION_MAP.get(value, value)


def translate_body_type(value):
    return BODY_TYPE_MAP.get(value, value)


def translate_drive_type(value):
    return DRIVE_TYPE_MAP.get(value, value)


def translate_color(value):
    return COLOR_MAP.get(value, value)


def translate_location(value):
    for jp, en in PREFECTURE_MAP.items():
        if jp in value:
            return en
    return value
