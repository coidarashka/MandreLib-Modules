// ==UserScript==
// @name         Кастомный баннер для итд.com
// @namespace    https://greasyfork.org/users/1270542
// @version      1.0.2
// @description  Добавляет кнопку «Загрузить изображение» в редактор баннера профиля на итд.com. Позволяет загрузить свою картинку и установить её как баннер (использует встроенный механизм сохранения сайта).
// @author       @sterepando
// @match        https://xn--d1ah4a.com/*
// @match        https://итд.com/*
// @grant        none
// @license      MIT
// ==/UserScript==

(function () {
    'use strict';

    // Функция добавления кнопки загрузки в модальное окно редактора
    function addLoadImageButton() {
        const modal = document.querySelector('.drawing-modal');
        if (!modal || modal.querySelector('#itd-custom-load-btn')) return;

        const canvas = modal.querySelector('.drawing-canvas');
        if (!canvas) return;

        // Создаём новую секцию в тулбаре
        const newSection = document.createElement('div');
        newSection.className = 'toolbar-section svelte-12bmgzp';

        const label = document.createElement('span');
        label.className = 'toolbar-label svelte-12bmgzp';
        label.textContent = 'Загрузка';

        const loadBtn = document.createElement('button');
        loadBtn.id = 'itd-custom-load-btn';
        loadBtn.className = 'action-btn svelte-12bmgzp';
        loadBtn.title = 'Загрузить своё изображение на холст';
        loadBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
        `;

        // Обработчик загрузки
        loadBtn.onclick = () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/png,image/jpeg,image/webp,image/gif';

            input.onchange = (e) => {
                const file = e.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = (ev) => {
                    const img = new Image();
                    img.onload = () => {
                        const ctx = canvas.getContext('2d');

                        // Очищаем холст
                        ctx.clearRect(0, 0, canvas.width, canvas.height);

                        // Масштабируем изображение по принципу cover (как фон)
                        const scale = Math.max(canvas.width / img.width, canvas.height / img.height);
                        const newWidth = img.width * scale;
                        const newHeight = img.height * scale;
                        const offsetX = (canvas.width - newWidth) / 2;
                        const offsetY = (canvas.height - newHeight) / 2;

                        ctx.drawImage(img, offsetX, offsetY, newWidth, newHeight);
                    };
                    img.src = ev.target.result;
                };
                reader.readAsDataURL(file);
            };

            input.click();
        };

        newSection.appendChild(label);
        newSection.appendChild(loadBtn);

        // Вставляем секцию после секции с инструментами (первая секция в тулбаре)
        const toolbar = modal.querySelector('.drawing-toolbar');
        const firstSection = toolbar.querySelector('.toolbar-section');
        if (firstSection && firstSection.nextSibling) {
            toolbar.insertBefore(newSection, firstSection.nextSibling);
        } else {
            toolbar.appendChild(newSection);
        }
    }

    // Отслеживаем появление модального окна редактора баннера
    const observer = new MutationObserver(() => {
        if (document.querySelector('.drawing-overlay')) {
            // Небольшая задержка, чтобы Svelte успел отрисовать содержимое
            setTimeout(addLoadImageButton, 200);
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // На случай, если модалка уже открыта при загрузке страницы
    if (document.querySelector('.drawing-overlay')) {
        setTimeout(addLoadImageButton, 500);
    }
})();