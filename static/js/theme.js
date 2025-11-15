// Chờ cho toàn bộ nội dung trang được tải xong
document.addEventListener('DOMContentLoaded', () => {

    // Dùng querySelectorAll để tìm TẤT CẢ các nút đổi theme (cả desktop và mobile)
    const themeToggles = document.querySelectorAll('#theme-toggle'); 
    const htmlElement = document.documentElement; // Đây chính là thẻ <html>
    const themeStorageKey = 'theme-preference'; // Tên key để lưu trong localStorage

    /**
     * Hàm này áp dụng giao diện (theme) được chỉ định.
     * Nó sẽ thêm/xóa class 'dark-mode' và cập nhật icon cho CẢ HAI nút bấm.
     */
    function applyTheme(theme) {
        if (theme === 'dark') {
            htmlElement.classList.add('dark-mode');
            // Cập nhật icon cho tất cả các nút
            themeToggles.forEach(btn => { btn.textContent = '☀️'; }); 
        } else {
            htmlElement.classList.remove('dark-mode');
            // Cập nhật icon cho tất cả các nút
            themeToggles.forEach(btn => { btn.textContent = '🌙'; });
        }
    }

    /**
     * Hàm này xử lý khi người dùng nhấn nút.
     * Nó sẽ đảo ngược giao diện hiện tại và lưu lựa chọn mới.
     */
    function toggleTheme() {
        // Kiểm tra xem <html> có class 'dark-mode' hay không
        const isDarkMode = htmlElement.classList.contains('dark-mode');
        
        // Nếu đang là 'dark' -> đổi sang 'light', và ngược lại
        const newTheme = isDarkMode ? 'light' : 'dark';

        // 1. Lưu lựa chọn mới vào localStorage
        localStorage.setItem(themeStorageKey, newTheme);
        
        // 2. Áp dụng giao diện mới
        applyTheme(newTheme);
    }

    /**
     * Hàm này tải giao diện "mặc định" khi trang vừa được mở.
     */
    function loadDefaultTheme() {
        // 1. Ưu tiên 1: Lấy lựa chọn đã lưu của người dùng
        const savedTheme = localStorage.getItem(themeStorageKey);
        
        if (savedTheme) {
            applyTheme(savedTheme);
            return; // Đã tìm thấy, dừng tại đây
        }

        // 2. Ưu tiên 2: Nếu người dùng chưa chọn, kiểm tra cài đặt OS
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        const systemTheme = systemPrefersDark ? 'dark' : 'light';
        applyTheme(systemTheme);
    }

    // --- CHẠY CÁC HÀM ---

    // 1. Gắn sự kiện 'click' cho TẤT CẢ các nút tìm thấy
    themeToggles.forEach(btn => {
        btn.addEventListener('click', toggleTheme);
    });

    // 2. Tải giao diện "mặc định" ngay khi trang được mở
    loadDefaultTheme();

});