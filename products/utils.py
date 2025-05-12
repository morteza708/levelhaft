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
        'ا': 'a', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ث': 's', 'ج': 'j', 'چ': 'ch',
        'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'z', 'ر': 'r', 'ز': 'z', 'ژ': 'zh',
        'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'z', 'ط': 't', 'ظ': 'z', 'ع': 'a',
        'غ': 'gh', 'ف': 'f', 'ق': 'gh', 'ک': 'k', 'گ': 'g', 'ل': 'l', 'م': 'm',
        'ن': 'n', 'و': 'v', 'ه': 'h', 'ی': 'y', ' ': '-', '_': '-'
    }
    return ''.join(persian_to_english.get(char, char) for char in text)

def create_persian_slug(text):
    # تبدیل اعداد فارسی به انگلیسی
    text = convert_to_english_digits(text)
    
    # اگر متن فارسی است، آن را به همان صورت نگه می‌داریم
    # اگر متن انگلیسی است، آن را به حروف کوچک تبدیل می‌کنیم
    if is_persian(text):
        text = text
    else:
        text = text.lower()
    
    # حذف فاصله‌ها و تبدیل به خط تیره
    text = text.strip().replace(' ', '-')
    
    # حذف کاراکترهای غیرمجاز
    allowed_chars = 'ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیءآاًهٔ' + 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' + '0123456789-'
    text = ''.join(c for c in text if c in allowed_chars or c == '-')
    
    # حذف خط تیره‌های تکراری
    while '--' in text:
        text = text.replace('--', '-')
    
    # حذف خط تیره از ابتدا و انتها
    return text.strip('-')