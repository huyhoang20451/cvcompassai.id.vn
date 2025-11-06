from bs4 import BeautifulSoup
import tinycss2
import re

# Đọc HTML
with open("cvcompassai.id.vn/templates/home_logged_in.html", "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "html.parser")

# Lấy tất cả class và id từ HTML
html_classes = set()
html_ids = set()
for tag in soup.find_all(True):
    if tag.has_attr("class"):
        for cls in tag["class"]:
            html_classes.add(cls)
    if tag.has_attr("id"):
        html_ids.add(tag["id"])

# Hàm kiểm tra selector có trong HTML không
def selector_in_html(selector):
    selector = selector.strip()
    parts = re.split(r'\s+|,', selector)
    for part in parts:
        if part.startswith(".") and part[1:] in html_classes:
            return True
        if part.startswith("#") and part[1:] in html_ids:
            return True
    return False

# Đọc CSS
with open("All.css", "r", encoding="utf-8") as f:
    css_content = f.read()

# Parse CSS
rules = tinycss2.parse_stylesheet(css_content, skip_comments=True, skip_whitespace=True)

filtered_css = ""

for rule in rules:
    if rule.type == 'qualified-rule':
        selector = tinycss2.serialize(rule.prelude).strip()
        if selector_in_html(selector):
            # Serialize block manually
            content = tinycss2.serialize(rule.content).strip()
            filtered_css += f"{selector} {{ {content} }}\n\n"

# Ghi CSS vào home.css
with open("cvcompassai.id.vn/static/css/home-logged-in.css", "w", encoding="utf-8") as f:
    f.write(filtered_css)

print("Đã lọc CSS chỉ dùng trong HTML vào home.css")
