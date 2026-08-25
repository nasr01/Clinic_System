(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        initMobileSidebar();
        initModals();
        initConfirmDialogs();
        initDoughnutCharts();
    });

    function initMobileSidebar() {
        var sidebar = document.querySelector('.sidebar');
        var overlay = document.querySelector('.sidebar-overlay');
        var toggleBtn = document.querySelector('.mobile-menu-btn');

        if (!sidebar || !toggleBtn) return;

        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            document.body.appendChild(overlay);
        }

        function openSidebar() {
            sidebar.classList.add('open');
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeSidebar() {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }

        toggleBtn.addEventListener('click', function () {
            if (sidebar.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });

        overlay.addEventListener('click', closeSidebar);

        window.addEventListener('resize', function () {
            if (window.innerWidth > 768) {
                closeSidebar();
            }
        });
    }

    function initModals() {
        var modalTriggers = document.querySelectorAll('[data-modal-target]');
        var modalCloses = document.querySelectorAll('[data-modal-close]');
        var backdrops = document.querySelectorAll('.modal-backdrop');

        modalTriggers.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                var targetId = btn.getAttribute('data-modal-target');
                var modal = document.getElementById(targetId);
                if (modal) {
                    modal.classList.add('active');
                    document.body.style.overflow = 'hidden';
                }
            });
        });

        modalCloses.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var backdrop = btn.closest('.modal-backdrop');
                if (backdrop) {
                    backdrop.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
        });

        backdrops.forEach(function (backdrop) {
            backdrop.addEventListener('click', function (e) {
                if (e.target === backdrop) {
                    backdrop.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal-backdrop.active').forEach(function (m) {
                    m.classList.remove('active');
                });
                document.body.style.overflow = '';
            }
        });
    }

    function initConfirmDialogs() {
        document.querySelectorAll('[data-confirm]').forEach(function (el) {
            el.addEventListener('click', function (e) {
                var message = el.getAttribute('data-confirm') || 'هل أنت متأكد؟';
                if (!confirm(message)) {
                    e.preventDefault();
                    return false;
                }
            });
        });
    }

    function initDoughnutCharts() {
        document.querySelectorAll('[data-doughnut]').forEach(function (canvas) {
            try {
                var data = JSON.parse(canvas.getAttribute('data-doughnut'));
                drawDoughnutChart(canvas, data);
            } catch (err) {
                console.warn('Chart parse error:', err);
            }
        });
    }

    function drawDoughnutChart(canvas, data) {
        var ctx = canvas.getContext('2d');
        var size = Math.min(canvas.parentElement.clientWidth - 40, 260);
        var dpr = window.devicePixelRatio || 1;

        canvas.width = size * dpr;
        canvas.height = size * dpr;
        canvas.style.width = size + 'px';
        canvas.style.height = size + 'px';
        ctx.scale(dpr, dpr);

        var cx = size / 2;
        var cy = size / 2;
        var outerRadius = (size / 2) - 8;
        var innerRadius = outerRadius * 0.62;

        var total = data.reduce(function (sum, item) {
            return sum + (item.value || 0);
        }, 0);

        var startAngle = -Math.PI / 2;

        if (total === 0) {
            ctx.beginPath();
            ctx.arc(cx, cy, outerRadius, 0, Math.PI * 2);
            ctx.arc(cx, cy, innerRadius, 0, Math.PI * 2, true);
            ctx.fillStyle = '#f1f5f9';
            ctx.fill();
            return;
        }

        data.forEach(function (item) {
            var value = item.value || 0;
            var sliceAngle = (value / total) * Math.PI * 2;
            var endAngle = startAngle + sliceAngle;

            if (value > 0) {
                ctx.beginPath();
                ctx.arc(cx, cy, outerRadius, startAngle, endAngle);
                ctx.arc(cx, cy, innerRadius, endAngle, startAngle, true);
                ctx.closePath();
                ctx.fillStyle = item.color || '#0d9488';
                ctx.fill();
            }

            startAngle = endAngle;
        });
    }

    window.openModal = function (id) {
        var modal = document.getElementById(id);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    };

    window.closeModal = function (id) {
        var modal = document.getElementById(id);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    };

    window.ClinicUI = {
        openModal: openModal,
        closeModal: closeModal
    };
})();
