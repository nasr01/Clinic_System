(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        initMobileSidebar();
        initModals();
        initConfirmDialogs();
        initDoughnutCharts();
        initNotifications();
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

    function initNotifications() {
        var wrapper = document.querySelector('.header-notification-wrapper');
        var bellBtn = document.getElementById('notificationBellBtn');
        var dropdown = document.getElementById('notificationsDropdown');

        if (!wrapper || !bellBtn || !dropdown) return;

        bellBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        });

        document.addEventListener('click', function(e) {
            if (!wrapper.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        updateNotificationCount();
        setInterval(updateNotificationCount, 30000);
    }

    window.toggleNotifications = function() {
        var dropdown = document.getElementById('notificationsDropdown');
        if (dropdown) {
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        }
    };

    // Global functions for notifications
    window.getCookie = function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    window.updateNotificationCount = function() {
        fetch('/doctor/notifications/count/')
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                var dot = document.getElementById('notificationDot');
                if (dot) {
                    dot.style.display = data.count === 0 ? 'none' : 'block';
                }

                var badge = document.getElementById('notificationBadge');
                if (data.count > 0) {
                    if (badge) {
                        badge.textContent = data.count;
                        badge.style.display = 'flex';
                    } else {
                        var bellBtn = document.getElementById('notificationBellBtn');
                        if (bellBtn) {
                            var newBadge = document.createElement('span');
                            newBadge.id = 'notificationBadge';
                            newBadge.className = 'notification-badge';
                            newBadge.textContent = data.count;
                            bellBtn.appendChild(newBadge);
                        }
                    }
                } else {
                    if (badge) {
                        badge.remove();
                    }
                }

                var sidebarCount = document.querySelector('.nav-link .notification-count');
                if (sidebarCount) {
                    if (data.count === 0) {
                        sidebarCount.style.display = 'none';
                    } else {
                        sidebarCount.textContent = data.count;
                        sidebarCount.style.display = 'inline-block';
                    }
                }

                var markAllBtn = document.getElementById('markAllReadBtn');
                if (markAllBtn && data.count === 0) {
                    markAllBtn.outerHTML = '<span class="notif-action-link notif-action-disabled">قراءة الكل</span>';
                } else if (!markAllBtn && data.count > 0) {
                    var header = document.querySelector('.notif-dropdown-header');
                    if (header) {
                        var existingDisabled = header.querySelector('.notif-action-disabled');
                        if (existingDisabled) {
                            var newBtn = document.createElement('button');
                            newBtn.type = 'button';
                            newBtn.id = 'markAllReadBtn';
                            newBtn.className = 'notif-action-link';
                            newBtn.textContent = 'قراءة الكل';
                            newBtn.onclick = function() { markAllNotificationsRead(); };
                            existingDisabled.outerHTML = newBtn.outerHTML;
                        }
                    }
                }
            })
            .catch(function(error) {
                console.warn('Failed to update notification count:', error);
            });
    };

    window.handleNotificationClick = function(notificationId, patientUrl) {
        fetch('/doctor/notifications/' + notificationId + '/read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                updateNotificationCount();
                var notifItems = document.querySelectorAll('.notif-item');
                notifItems.forEach(function(item) {
                    if (item.getAttribute('onclick') && item.getAttribute('onclick').indexOf(notificationId) !== -1) {
                        item.classList.remove('notif-item-unread');
                        var dot = item.querySelector('.notif-item-dot');
                        if (dot) dot.remove();
                    }
                });
                if (patientUrl) {
                    setTimeout(function() {
                        window.location.href = patientUrl;
                    }, 200);
                }
            }
        })
        .catch(function(error) {
            console.warn('Failed to mark notification read:', error);
            if (patientUrl) {
                window.location.href = patientUrl;
            }
        });
    };

    window.markAllNotificationsRead = function() {
        fetch('/doctor/notifications/read-all/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                updateNotificationCount();
                document.querySelectorAll('.notif-item-unread').forEach(function(el) {
                    el.classList.remove('notif-item-unread');
                });
                document.querySelectorAll('.notif-item-dot').forEach(function(el) {
                    el.remove();
                });
                var markAllBtn = document.getElementById('markAllReadBtn');
                if (markAllBtn) {
                    markAllBtn.outerHTML = '<span class="notif-action-link notif-action-disabled">قراءة الكل</span>';
                }
            }
        })
        .catch(function(error) {
            console.warn('Failed to mark all notifications read:', error);
        });
    };

    window.refreshNotifications = function() {
        var dropdown = document.getElementById('notificationsDropdown');
        if (dropdown) {
            var body = dropdown.querySelector('.notif-dropdown-body');
            if (body) {
                var oldHTML = body.innerHTML;
                body.style.opacity = '0.5';
                setTimeout(function() {
                    body.style.opacity = '1';
                }, 300);
            }
        }
        updateNotificationCount();
        setTimeout(function() {
            location.reload();
        }, 300);
    };
})();
