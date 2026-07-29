"""Site-wide middleware helpers."""

GA_MEASUREMENT_ID = "G-VK29QNQ94H"

_GA_SNIPPET = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{id}');
</script>
""".format(id=GA_MEASUREMENT_ID)


class GoogleAnalyticsMiddleware:
    """Injects the GA4 gtag snippet right after <head> on every HTML page.

    Site templates don't share a single base, so this guarantees coverage
    across landing, dashboards, admin and error pages in one place. Non-HTML,
    streaming, and already-tagged responses are left untouched.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if getattr(response, "streaming", False):
                return response
            if "text/html" not in response.get("Content-Type", ""):
                return response
            if not hasattr(response, "content"):
                return response

            charset = response.charset or "utf-8"
            content = response.content.decode(charset, errors="ignore")
            if GA_MEASUREMENT_ID in content:
                return response

            idx = content.lower().find("<head>")
            if idx == -1:
                return response

            insert_at = idx + len("<head>")
            content = content[:insert_at] + "\n" + _GA_SNIPPET + content[insert_at:]
            response.content = content.encode(charset)
            if response.has_header("Content-Length"):
                response["Content-Length"] = str(len(response.content))
        except Exception:
            # Analytics must never break a page render.
            pass
        return response
