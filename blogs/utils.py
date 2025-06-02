def convert_to_english_digits(text):
    if not isinstance(text, str):
        text = str(text)
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return text.translate(translation_table).replace('٬', '').replace(',', '').strip()

def is_persian(text):
    # محدوده کاراکترهای فارسی در یونیکد
    persian_range = range(0x0600, 0x06FF + 1)
    return any(ord(c) in persian_range for c in text)

def persian_to_english_char(text):
    persian_to_english = {
        'ا': 'a', 'آ': 'a', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ث': 's', 'ج': 'j', 'چ': 'ch',
        'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'z', 'ر': 'r', 'ز': 'z', 'ژ': 'zh',
        'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'z', 'ط': 't', 'ظ': 'z', 'ع': 'a',
        'غ': 'gh', 'ف': 'f', 'ق': 'gh', 'ک': 'k', 'گ': 'g', 'ل': 'l', 'م': 'm',
        'ن': 'n', 'و': 'v', 'ه': 'h', 'ی': 'y', 'ي': 'y', 'ة': 'h', 'ئ': 'y', 'إ': 'e', 'أ': 'a', 'ؤ': 'v', 'ى': 'a',
        ' ': '-', '_': '-'
    }
    return ''.join(persian_to_english.get(char, char) for char in text)

def persian_to_english(text):
    if not text:
        return ''
    # تبدیل اعداد فارسی به انگلیسی
    text = convert_to_english_digits(text)
    # تبدیل حروف فارسی به فینگلیش
    text = persian_to_english_char(text)
    # حذف کاراکترهای غیرمجاز (فقط حروف انگلیسی، اعداد و خط تیره)
    import re
    text = re.sub(r'[^a-zA-Z0-9-]', '', text)
    text = text.lower()
    while '--' in text:
        text = text.replace('--', '-')
    return text.strip('-')