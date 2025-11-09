/**
 * SCRIPT TẢI CÀI ĐẶT
 * Script này phải được đặt trong <head> của TẤT CẢ các trang
 * để áp dụng theme/font trước khi trang hiển thị, tránh bị "nháy" (flicker).
 */
(function() {
    // 1. Áp dụng Theme
    const savedTheme = localStorage.getItem('theme') || 'system'; // Mặc định là 'system'
    
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark-theme');
    } else if (savedTheme === 'light') {
        document.documentElement.classList.add('light-theme');
    } else if (savedTheme === 'system') {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.classList.add('dark-theme');
        } else {
            document.documentElement.classList.add('light-theme');
        }
    }

    // 2. Áp dụng Font
    const savedFont = localStorage.getItem('font');
    if (savedFont) {
        document.documentElement.style.fontFamily = savedFont;
    }

})();