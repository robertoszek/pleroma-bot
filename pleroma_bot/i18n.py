import os
import gettext

localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "locale")
translate = gettext.translation("pleroma_bot", localedir, fallback=True)
_ = translate.gettext
