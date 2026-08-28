import './assets/style.css';
import $ from 'jquery';

import { getCookie, getMe, logout, User, handleNotifications } from './api';
import instructionsHtml from './assets/instructions.html';
import { esc as escHtml } from './utils';

$(async () => {
    $('#instructions-box').html(instructionsHtml);

    if (getCookie('ltb_token')) {
        try {
            const user = await getMe();
            showRoleButtons(user);
            
            const params = new URLSearchParams(window.location.search);
            if (params.get('registered') != null) {
                const msg = $('<span style="color: #19632e;">Registration successful; please contribute below.</span><br>');
                $('#role-buttons').prepend(msg);
                
                const url = new URL(window.location.href);
                // url.searchParams.delete('registered');
                window.history.replaceState({}, document.title, url.toString());
            }
        } catch {
            $('#auth-error').show();
        }
    } else {
        $('#cta-info-unauth').show();
    }
});

function showRoleButtons(user: User): void {
    $('#register-btn').hide();
    $('#cta-info-unauth').hide();

    const container = $('#role-buttons');
    const actions1 = $('<div class="role-actions"></div>');
    const actions2 = $('<div class="role-actions" style="margin-top: 10px;"></div>');

    container.append(`<span>Hello ${escHtml(user.name)} from ${escHtml(user.affiliation)}!</span><br><br>`);

    if (user.roles.includes('contributor')) {
        actions1.append('<a href="contribute" class="btn btn-success">✍️&nbsp;Contribute examples</a>');
    }
    if (user.roles.includes('reviewer')) {
        actions1.append('<a href="review" class="btn btn-success">🔍&nbsp;Review examples</a>');
    }

    actions1.append('<a href="contributors" class="btn btn-success">Contributors</a>');
    // actions1.append('<a href="leaderboard-results" class="btn btn-success">Leaderboard</a>');
    // actions1.append('<a href="leaderboard-submission" class="btn btn-success">Submit model</a>');
    if (user.roles.includes('admin')) {
        actions2.append('<a href="admin" class="btn btn-success">Admin</a>');
    }

    actions2.append('<a href="profile" class="btn btn-success">Profile</a>');

    const logoutBtn = $('<button class="btn btn-success">Logout</button>');
    logoutBtn.on('click', logout);
    actions2.append(logoutBtn);

    container.append(actions1);
    container.append(actions2);

    container.css('display', 'block');

    if (user.notifications.length > 0) {
        const notifBox = $('#notifications-box');
        notifBox.empty();
        
        const clearBtn = $('<button class="btn-underlined" style="font-size: 0.8em;">Clear Notifications</button>');
        clearBtn.on('click', async () => {
            await handleNotifications('clear');
            notifBox.hide();
        });
        
        user.notifications.reverse().forEach(n => {
            const item = $('<div>').css({
                padding: '10px', fontSize: '0.9em',
                background: n.status === 'unread' ? '#ddd' : 'transparent', textAlign: 'left',
            });
            item.html(`<strong>${escHtml(n.type)}</strong>: <span style="color:#444">${escHtml(n.content)}</span> <small style="color:#aaa; float:right;">${escHtml(n.created)}</small>`);
            notifBox.append(item);
        });
        notifBox.append(clearBtn);
        
        notifBox.show();

        const hasUnread = user.notifications.some(n => n.status === 'unread');
        if (hasUnread) {
            handleNotifications('view').catch(console.error);
        }
    }
}
