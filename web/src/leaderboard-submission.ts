import './assets/style.css';
import $ from 'jquery';
import { getCookie, getMe, renderRoleSwitcher } from './api';
import { renderHeaderStatus } from './utils';

$(async () => {
    if (getCookie('ltb_token')) {
        try {
            const currentUser = await getMe();
            renderHeaderStatus(currentUser);
            renderRoleSwitcher(currentUser.roles);
        } catch {
            // ignore error, just don't show user info
        }
    }

    $('#submission-form').on('submit', async (e) => {
        e.preventDefault();

        const fileInput = document.getElementById('submission-file') as HTMLInputElement;
        if (!fileInput.files || fileInput.files.length === 0) return;
        
        const file = fileInput.files[0];
        const reader = new FileReader();

        reader.onload = async (event) => {
            try {
                const fileContent = event.target?.result as string;
                const jsonData = JSON.parse(fileContent);

                const releaseYear = $('#model-release-year').val();
                const releaseMonth = String($('#model-release-month').val()).padStart(2, '0');

                const payload = {
                    submission: jsonData,
                    model_name: $('#model-name').val(),
                    model_size: $('#model-size').val(),
                    model_release: `${releaseYear}-${releaseMonth}`,
                    model_description: $('#model-description').val(),
                    institution: $('#institution').val(),
                    submitter_email: $('#submitter-email').val(),
                    mode: $('#competition-mode').val()
                };

                const statusEl = $('#submit-status');
                const btn = $('#submit-btn');

                statusEl.text('Submitting...').css('color', 'black');
                btn.prop('disabled', true);

                const response = await fetch('/api/leaderboard', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    throw new Error('Server returned ' + response.status);
                }

                statusEl.text('Submission successful!').css('color', 'green');
                ($('#submission-form')[0] as HTMLFormElement).reset();
            } catch (err) {
                console.error(err);
                $('#submit-status').text('Error submitting or parsing JSON.').css('color', 'red');
            } finally {
                $('#submit-btn').prop('disabled', false);
            }
        };

        reader.readAsText(file);
    });
});
