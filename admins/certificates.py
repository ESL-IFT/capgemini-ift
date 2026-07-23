"""Certificate generation for IFT.

Renders a student's name onto a certificate template and returns a print-ready
PDF (RGB, colour-accurate). Templates live in ``static/certificates/`` and the
name is set in the "Dancing Script" font bundled at ``static/fonts/``.

The source templates are CMYK JPGs with an embedded "U.S. Web Coated (SWOP) v2"
ICC profile. We convert CMYK -> sRGB using that profile via ImageCms so colours
stay accurate (a naive PIL convert shifts purple -> blue) and the delivered PDF
renders correctly in every viewer / phone.
"""
import io
from django.conf import settings
from PIL import Image, ImageCms, ImageDraw, ImageFont

# The school-champion template is a very large (18k x 14k) image; lift PIL's
# decompression-bomb guard so it can be opened.
Image.MAX_IMAGE_PIXELS = None

_CERT_DIR = settings.BASE_DIR / 'static' / 'certificates'
_FONT_PATH = settings.BASE_DIR / 'static' / 'fonts' / 'DancingScript.ttf'

# Name-centre position as a fraction of (width, height), the max name width as a
# fraction of width, and whether the source is already RGB. Values were tuned
# visually against each template.
CERTIFICATE_TYPES = {
    'participation': {
        'label': 'Participation (Idea Submission)',
        'description': 'Sent to every student who submits an idea.',
        'file': 'participation.jpg',
        'fx': 0.688, 'fy': 0.417, 'maxw': 0.30, 'is_rgb': False,
        'active': True,
    },
    'top100': {
        'label': 'Top 100',
        'description': 'Sent to students ranked in the Top 100.',
        'file': 'top100.jpg',
        'fx': 0.675, 'fy': 0.432, 'maxw': 0.30, 'is_rgb': False,
        'active': True,
    },
    'top400': {
        'label': 'Top 400',
        'description': 'Sent to students ranked in the Top 400.',
        'file': 'top400.jpg',
        'fx': 0.688, 'fy': 0.410, 'maxw': 0.30, 'is_rgb': False,
        'active': True,
    },
    # Goes to the SCHOOL (one per school, school name overlaid) when it has a
    # student in the Top 100.
    'school_champion': {
        'label': 'School Champion (Top 100)',
        'description': 'Sent to each school that has a Top-100 student.',
        'file': 'school-champion.jpg',
        'fx': 0.505, 'fy': 0.545, 'maxw': 0.34, 'is_rgb': True,
        'active': True,
    },
}

# Email subject/body per certificate type. {name} is the recipient's name.
EMAIL_COPY = {
    'participation': {
        'subject': 'India\'s Future Tycoons — Certificate of Participation',
        'body': (
            'Certificate of Participation\n\n'
            'This is to certify that {name} has successfully participated in '
            'the India\'s Future Tycoons challenge by submitting an innovative '
            'venture idea and demonstrating entrepreneurial thinking and '
            'creativity.\n\n'
            'Please find your certificate attached.\n\n'
            'Warm regards,\n'
            'Team IFT — Tata ClassEdge | ENpower'
        ),
    },
    'top100': {
        'subject': 'India\'s Future Tycoons — Certificate of Achievement (Top 100)',
        'body': (
            'Certificate of Achievement — India\'s TOP 100\n\n'
            'This is to certify that {name} has successfully qualified as one '
            'of India\'s TOP 100 Teams in the India\'s Future Tycoons challenge '
            'for demonstrating exceptional innovation, creativity, and '
            'entrepreneurial excellence through an outstanding venture idea.\n\n'
            'Please find your certificate attached.\n\n'
            'Warm regards,\n'
            'Team IFT — Tata ClassEdge | ENpower'
        ),
    },
    'top400': {
        'subject': 'India\'s Future Tycoons — Certificate of Achievement (Top 400)',
        'body': (
            'Certificate of Achievement — India\'s TOP 400\n\n'
            'This is to certify that {name} has successfully qualified as one '
            'of India\'s TOP 400 Teams in the India\'s Future Tycoons challenge '
            'for building an innovative and impactful venture idea.\n\n'
            'Please find your certificate attached.\n\n'
            'Warm regards,\n'
            'Team IFT — Tata ClassEdge | ENpower'
        ),
    },
    'school_champion': {
        'subject': 'India\'s Future Tycoons — Certificate of Excellence',
        'body': (
            'Certificate of Excellence\n\n'
            'This certificate is proudly presented to {name} in recognition of '
            'its outstanding contribution to nurturing innovation and '
            'entrepreneurship, with students successfully qualifying among '
            'India\'s TOP 100 Teams in the India\'s Future Tycoons challenge.\n\n'
            'Your commitment to inspiring young innovators and fostering '
            'entrepreneurial excellence is sincerely appreciated.\n\n'
            'Please find your certificate attached.\n\n'
            'Warm regards,\n'
            'Team IFT — Tata ClassEdge | ENpower'
        ),
    },
}

# Reused sRGB target profile (cheap to keep around).
_SRGB = ImageCms.createProfile('sRGB')


def active_certificate_types():
    """cert_type -> config for the types the admin may send right now."""
    return {k: v for k, v in CERTIFICATE_TYPES.items() if v.get('active')}


def student_display_name(student):
    """Proper full name: First [Middle] Last, falling back to what exists."""
    user = student.user
    parts = [user.first_name, getattr(student, 'middle_name', ''), user.last_name]
    name = ' '.join(p.strip() for p in parts if p and p.strip())
    return name or user.get_full_name() or user.username


def _load_rgb_template(cfg):
    """Open a template and return it as an accurate sRGB image."""
    img = Image.open(_CERT_DIR / cfg['file'])
    if cfg['is_rgb'] or img.mode == 'RGB':
        return img.convert('RGB')
    icc = img.info.get('icc_profile')
    if icc:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        return ImageCms.profileToProfile(
            img, src, _SRGB, renderingIntent=0, outputMode='RGB'
        )
    return img.convert('RGB')


def _fit_font(draw, text, target_w, target_h):
    """Largest font size (weight 600) whose text fits target_w x target_h."""
    best = 10
    size = 10
    while size < 900:
        f = ImageFont.truetype(str(_FONT_PATH), size)
        try:
            f.set_variation_by_axes([600])
        except Exception:
            pass
        bb = draw.textbbox((0, 0), text, font=f)
        if (bb[2] - bb[0]) > target_w or (bb[3] - bb[1]) > target_h:
            break
        best = size
        size += 2
    f = ImageFont.truetype(str(_FONT_PATH), best)
    try:
        f.set_variation_by_axes([600])
    except Exception:
        pass
    return f


# Cap the render width so an oversized template (school-champion.jpg is
# 18759px wide) doesn't produce a 6+ MB PDF that's awkward to email. The three
# main templates are already 3509px, so this is a no-op for them. Placement is
# fraction-based, so it is unaffected by scaling.
_MAX_RENDER_WIDTH = 3600


def render_certificate_image(name, cert_type):
    """Return an RGB PIL image of the certificate with ``name`` overlaid."""
    cfg = CERTIFICATE_TYPES[cert_type]
    img = _load_rgb_template(cfg)
    if img.width > _MAX_RENDER_WIDTH:
        img.thumbnail((_MAX_RENDER_WIDTH, img.height), Image.LANCZOS)
    W, H = img.size
    draw = ImageDraw.Draw(img)

    cx, cy = int(W * cfg['fx']), int(H * cfg['fy'])
    font = _fit_font(draw, name, W * cfg['maxw'], H * 0.11)
    bb = draw.textbbox((0, 0), name, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((cx - tw // 2 - bb[0], cy - th // 2 - bb[1]),
              name, fill=(0, 0, 0), font=font)
    return img


def generate_certificate_pdf(name, cert_type):
    """Return certificate PDF bytes for ``name`` and ``cert_type``."""
    img = render_certificate_image(name, cert_type)
    buf = io.BytesIO()
    img.save(buf, 'PDF', resolution=150.0)
    return buf.getvalue()


def certificate_filename(name, cert_type):
    """Safe attachment filename, e.g. 'IFT_Top_100_Shravani_Todankar.pdf'."""
    label = CERTIFICATE_TYPES[cert_type]['label']
    safe = ''.join(c if c.isalnum() else '_' for c in f'{label}_{name}')
    safe = '_'.join(filter(None, safe.split('_')))
    return f'IFT_{safe}.pdf'
