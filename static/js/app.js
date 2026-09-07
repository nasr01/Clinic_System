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
            var isHidden = dropdown.style.display === 'none' || dropdown.style.display === '';
            dropdown.style.display = isHidden ? 'block' : 'none';
            if (isHidden) {
                markDropdownNotificationsAsRead();
            }
        });

        document.addEventListener('click', function(e) {
            if (!wrapper.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        updateNotificationCount();
        setInterval(updateNotificationCount, 30000);
    }

    function markDropdownNotificationsAsRead() {
        var unreadItems = document.querySelectorAll('#notificationsDropdown .notif-item-unread');
        if (unreadItems.length === 0) return;

        fetch('/doctor/notifications/read-all/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                unreadItems.forEach(function(item) {
                    item.classList.remove('notif-item-unread');
                    var dot = item.querySelector('.notif-item-dot');
                    if (dot) dot.remove();
                    showNotificationDeleteBtn(item);
                });
                updateNotificationCount();
                refreshClearReadBtn();
            }
        })
        .catch(function(err) {
            console.warn('Mark dropdown read failed:', err);
        });
    }

    function showNotificationDeleteBtn(item) {
        var btn = item.querySelector('.notif-delete-btn');
        if (btn) {
            btn.style.display = 'flex';
        }
    }

    window.toggleNotifications = function() {
        var dropdown = document.getElementById('notificationsDropdown');
        if (dropdown) {
            var isHidden = dropdown.style.display === 'none' || dropdown.style.display === '';
            dropdown.style.display = isHidden ? 'block' : 'none';
            if (isHidden) {
                markDropdownNotificationsAsRead();
            }
        }
    };

    window.getCookie = function(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
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
            .then(function(response) { return response.json(); })
            .then(function(data) {
                var dot = document.getElementById('notificationDot');
                if (dot) {
                    dot.style.display = data.count === 0 ? 'none' : 'block';
                }

                var bellBtn = document.getElementById('notificationBellBtn');
                var badge = document.getElementById('notificationBadge');
                if (data.count > 0) {
                    if (badge) {
                        badge.textContent = data.count > 99 ? '99+' : data.count;
                        badge.style.display = 'flex';
                    } else if (bellBtn) {
                        var newBadge = document.createElement('span');
                        newBadge.id = 'notificationBadge';
                        newBadge.className = 'notification-badge';
                        newBadge.textContent = data.count > 99 ? '99+' : data.count;
                        bellBtn.appendChild(newBadge);
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
                        sidebarCount.textContent = data.count > 99 ? '99+' : data.count;
                        sidebarCount.style.display = 'inline-block';
                    }
                }

                refreshMarkAllBtn(data.count);
                refreshClearReadBtn();
            })
            .catch(function(error) {
                console.warn('Failed to update notification count:', error);
            });
    };

    function refreshMarkAllBtn(count) {
        var markAllBtn = document.getElementById('markAllReadBtn');
        var header = document.querySelector('.notif-dropdown-header');
        if (!header) return;

        if (count === 0) {
            if (markAllBtn) {
                markAllBtn.outerHTML = '<span class="notif-action-link notif-action-disabled" id="markAllReadPlaceholder">قراءة الكل</span>';
            }
        } else {
            var placeholder = document.getElementById('markAllReadPlaceholder');
            if (placeholder) {
                var newBtn = document.createElement('button');
                newBtn.type = 'button';
                newBtn.id = 'markAllReadBtn';
                newBtn.className = 'notif-action-link';
                newBtn.textContent = 'قراءة الكل';
                newBtn.onclick = function() { markAllNotificationsRead(); };
                placeholder.outerHTML = newBtn.outerHTML;
                var rebind = document.getElementById('markAllReadBtn');
                if (rebind) rebind.onclick = function() { markAllNotificationsRead(); };
            }
        }
    }

    function refreshClearReadBtn() {
        var footer = document.querySelector('.notif-dropdown-footer');
        if (!footer) return;
        var readItems = document.querySelectorAll('#notificationsDropdown .notif-item:not(.notif-item-unread)');
        var hasRead = readItems.length > 0;
        var clearBtn = document.getElementById('clearReadBtn');

        if (hasRead) {
            if (!clearBtn) {
                var btn = document.createElement('button');
                btn.type = 'button';
                btn.id = 'clearReadBtn';
                btn.className = 'notif-action-link';
                btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/></svg> مسح المقروءة';
                btn.onclick = function() { clearReadNotifications(); };
                footer.insertBefore(btn, footer.firstChild);
            }
        } else {
            if (clearBtn) clearBtn.remove();
        }
    }

    window.handleNotificationClick = function(notificationId, patientUrl) {
        fetch('/doctor/notifications/' + notificationId + '/read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                updateNotificationCount();
                var notifItems = document.querySelectorAll('.notif-item');
                notifItems.forEach(function(item) {
                    var attr = item.getAttribute('data-notification-id');
                    if (attr && String(attr) === String(notificationId)) {
                        item.classList.remove('notif-item-unread');
                        var dot = item.querySelector('.notif-item-dot');
                        if (dot) dot.remove();
                        showNotificationDeleteBtn(item);
                    }
                });
                refreshClearReadBtn();
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

    window.deleteSingleNotification = function(notificationId, event) {
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        if (!confirm('هل تريد حذف هذا الإشعار؟')) return;

        fetch('/doctor/notifications/' + notificationId + '/delete/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                var items = document.querySelectorAll('[data-notification-id="' + notificationId + '"]');
                items.forEach(function(item) {
                    item.style.transition = 'all 0.2s ease';
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(20px)';
                    setTimeout(function() {
                        item.remove();
                        checkNotificationsEmpty();
                        refreshClearReadBtn();
                    }, 200);
                });
                updateNotificationCount();
            } else {
                alert(data.error || 'تعذر حذف الإشعار');
            }
        })
        .catch(function(err) {
            console.warn('Delete notification failed:', err);
        });
    };

    window.clearReadNotifications = function() {
        if (!confirm('هل تريد حذف جميع الإشعارات المقروءة؟')) return;

        fetch('/doctor/notifications/clear-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                var readItems = document.querySelectorAll('#notificationsDropdown .notif-item:not(.notif-item-unread)');
                readItems.forEach(function(item) {
                    item.style.transition = 'all 0.2s ease';
                    item.style.opacity = '0';
                    setTimeout(function() { item.remove(); }, 200);
                });
                setTimeout(function() {
                    checkNotificationsEmpty();
                    refreshClearReadBtn();
                }, 250);
                updateNotificationCount();
            }
        })
        .catch(function(err) {
            console.warn('Clear read notifications failed:', err);
        });
    };

    function checkNotificationsEmpty() {
        var body = document.querySelector('#notificationsDropdown .notif-dropdown-body');
        if (!body) return;
        var items = body.querySelectorAll('.notif-item');
        if (items.length === 0) {
            body.innerHTML = '<div class="notif-empty">' +
                '<div class="notif-empty-icon">' +
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>' +
                '</div>' +
                '<span>لا توجد إشعارات جديدة</span>' +
                '<small>سيتم عرض الإشعارات هنا عند وصولها</small>' +
                '</div>';
        }
    }

    window.markAllNotificationsRead = function() {
        fetch('/doctor/notifications/read-all/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                updateNotificationCount();
                document.querySelectorAll('.notif-item-unread').forEach(function(el) {
                    el.classList.remove('notif-item-unread');
                    showNotificationDeleteBtn(el);
                });
                document.querySelectorAll('.notif-item-dot').forEach(function(el) {
                    el.remove();
                });
                refreshClearReadBtn();
            }
        })
        .catch(function(error) {
            console.warn('Failed to mark all notifications read:', error);
        });
    };

    window.refreshNotifications = function() {
        updateNotificationCount();
        setTimeout(function() {
            location.reload();
        }, 300);
    };
})();
