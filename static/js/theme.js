(function(){
    // Small settings manager: theme, font, language. Persists via cookie + localStorage when available.
    function getCookie(name){
        const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return m ? decodeURIComponent(m.pop()) : null;
    }
    function setCookie(name, value, days){
        let expires = '';
        if(days){
            const d = new Date();
            d.setTime(d.getTime() + (days*24*60*60*1000));
            expires = '; expires=' + d.toUTCString();
        }
        document.cookie = name + '=' + encodeURIComponent(value || '') + expires + '; path=/';
    }

    function showToast(message, ms){
        try{
            ms = ms || 2200;
            let t = document.getElementById('theme-toast');
            if(!t){
                t = document.createElement('div');
                t.id = 'theme-toast';
                t.style.position = 'fixed';
                t.style.right = '20px';
                t.style.bottom = '20px';
                t.style.background = 'rgba(0,0,0,0.75)';
                t.style.color = '#fff';
                t.style.padding = '10px 14px';
                t.style.borderRadius = '8px';
                t.style.zIndex = 9999;
                t.style.fontSize = '13px';
                t.style.transition = 'opacity .25s ease';
                document.body.appendChild(t);
            }
            t.textContent = message;
            t.style.opacity = '1';
            clearTimeout(t._hideTimer);
            t._hideTimer = setTimeout(()=>{ t.style.opacity = '0'; }, ms);
        }catch(e){ /* ignore */ }
    }

    // storage helpers for theme/font/lang
    function getStored(key, cookieName, fallback){
        const c = getCookie(cookieName);
        try{ return c || (window.localStorage && localStorage.getItem(key)) || fallback; }catch(e){ return c || fallback; }
    }
    function setStored(key, cookieName, value){
        try{ setCookie(cookieName, value, 365); }catch(e){}
        try{ if(window.localStorage) localStorage.setItem(key, value); }catch(e){}
    }

    // applyers
    function applyTheme(theme){
        const html = document.documentElement;
        if(theme === 'dark'){
            html.classList.add('theme-dark');
            html.classList.remove('theme-light');
        } else {
            html.classList.add('theme-light');
            html.classList.remove('theme-dark');
        }
    }
    function applyFont(font){
        try{ document.documentElement.style.setProperty('--site-font-family', font); document.documentElement.style.fontFamily = font; }catch(e){}
    }
    function applyLang(lang){
        try{ document.documentElement.lang = lang || 'vi'; }catch(e){}
    }

    // public API
    window.setSiteTheme = function(theme){ setStored('site_theme','site_theme', theme); applyTheme(theme); };
    window.getSiteTheme = function(){ return getStored('site_theme','site_theme','light'); };
    window.resetSiteTheme = function(){ try{ setCookie('site_theme','',-1); }catch(e){} try{ localStorage.removeItem('site_theme'); }catch(e){} applyTheme('light'); showToast('Đã đặt lại giao diện về mặc định.'); };

    window.setSiteFont = function(font){ setStored('site_font','site_font', font); applyFont(font); };
    window.getSiteFont = function(){ return getStored('site_font','site_font','Noto Sans'); };
    window.resetSiteFont = function(){ try{ setCookie('site_font','',-1); }catch(e){} try{ localStorage.removeItem('site_font'); }catch(e){} applyFont('Noto Sans'); showToast('Đã đặt lại kiểu chữ về mặc định.'); };

    window.setSiteLang = function(lang){ setStored('site_lang','site_lang', lang); applyLang(lang); };
    window.getSiteLang = function(){ return getStored('site_lang','site_lang','vi'); };
    window.resetSiteLang = function(){ try{ setCookie('site_lang','',-1); }catch(e){} try{ localStorage.removeItem('site_lang'); }catch(e){} applyLang('vi'); showToast('Đã đặt lại ngôn ngữ về mặc định.'); };

    // reset everything
    window.resetAllSiteSettings = function(){ window.resetSiteTheme(); window.resetSiteFont(); window.resetSiteLang(); };

    // init on load
    function initAll(){
        try{ applyTheme(window.getSiteTheme()); }catch(e){}
        try{ applyFont(window.getSiteFont()); }catch(e){}
        try{ applyLang(window.getSiteLang()); }catch(e){}
    }

    function initControls(){
        // theme controls
        const themeSelect = document.querySelector('select[name="theme"]');
        const themeRadios = document.querySelectorAll('input[type="radio"][name="theme"]');
        const currentTheme = window.getSiteTheme();
        if(themeSelect){ themeSelect.value = currentTheme; themeSelect.addEventListener('change', function(){ window.setSiteTheme(this.value); showToast('Giao diện: ' + this.value); }); }
        if(themeRadios && themeRadios.length){ themeRadios.forEach(r=>{ if(r.value === currentTheme) r.checked = true; r.addEventListener('change', function(){ if(this.checked){ window.setSiteTheme(this.value); showToast('Giao diện: ' + this.value); } }); }); }

        // font controls
        const fontSelect = document.querySelector('select[name="font"]');
        const currentFont = window.getSiteFont();
        const preview = document.getElementById('preview-box');
        if(fontSelect){
            fontSelect.value = currentFont;
            fontSelect.addEventListener('change', function(){ window.setSiteFont(this.value); if(preview) preview.style.fontFamily = this.value; showToast('Kiểu chữ: ' + this.value); });
        }
        if(preview){ preview.style.fontFamily = currentFont; }

        // language controls
        const langRadios = document.querySelectorAll('input[type="radio"][name="lang"]');
        const currentLang = window.getSiteLang();
        if(langRadios && langRadios.length){ langRadios.forEach(r=>{ if(r.value === currentLang) r.checked = true; r.addEventListener('change', function(){ if(this.checked){ window.setSiteLang(this.value); showToast('Ngôn ngữ: ' + (this.value==='vi'?'Tiếng Việt':'English')); } }); }); }

        // Save and Reset
        const saveBtn = document.querySelector('.save-btn');
        const resetBtn = document.querySelector('.reset-btn');
        if(saveBtn){ saveBtn.addEventListener('click', function(e){ e.preventDefault(); showToast('Cài đặt đã được lưu.'); }); }
        if(resetBtn){ resetBtn.addEventListener('click', function(e){ e.preventDefault(); window.resetAllSiteSettings(); }); }
    }

    if(document.readyState === 'loading'){
        document.addEventListener('DOMContentLoaded', function(){ initAll(); initControls(); });
    } else { initAll(); initControls(); }

})();
