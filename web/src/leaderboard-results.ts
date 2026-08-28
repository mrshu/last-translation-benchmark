import './assets/style.css';
import $ from 'jquery';
import { fetchLeaderboardResults, getMe, renderRoleSwitcher } from './api';
import { renderHeaderStatus } from './utils';

interface Submission {
    id: number;
    source_lang: string;
    target_lang: string;
    non_text: string | null;
    tags: string[];
}

interface ModelInfo {
    institution: string;
    submitter_email: string;
    model_name: string;
    model_size: string;
    mode: string;
    [key: string]: any;
}

interface ModelResult {
    id: number;
    info: ModelInfo;
    results: Record<string, number>;
}

interface LeaderboardData {
    submissions: Submission[];
    models: ModelResult[];
}

let rawData: LeaderboardData | null = null;

async function loadLeaderboard() {
    try {
        rawData = await fetchLeaderboardResults();
        populateLanguageFilter();
        renderTable();
    } catch (e) {
        console.error(e);
        $('#leaderboard-content').html(`<div class="empty">Failed to load leaderboard data: ${e}</div>`);
    }
}

function populateLanguageFilter() {
    if (!rawData) return;
    const langs = new Set<string>();
    for (const item of rawData.submissions) {
        if (item.source_lang) langs.add(item.source_lang);
        if (item.target_lang) langs.add(item.target_lang);
    }
    
    const sortedLangs = Array.from(langs).sort();
    const select = $('#filter-lang');
    for (const lang of sortedLangs) {
        select.append(`<option value="${lang}">${lang}</option>`);
    }
}

function renderTable() {
    if (!rawData) return;

    const filterMode = $('#filter-mode').val() as string;
    const filterTag = $('#filter-tag').val() as string;
    const filterMedia = $('#filter-media').val() as string;
    const filterLang = $('#filter-lang').val() as string;

    // Filter benchmark items
    const activeItems = rawData.submissions.filter(item => {
        // Tag filter (subset)
        if (filterTag !== 'all' && !item.tags.includes(filterTag)) return false;

        // Media filter
        if (filterMedia === 'text' && item.non_text !== null) return false;
        if (filterMedia === 'non-text' && item.non_text === null) return false;

        // Language filter
        if (filterLang !== 'all') {
            if (item.source_lang !== filterLang && item.target_lang !== filterLang) {
                return false;
            }
        }

        return true;
    });

    if (activeItems.length === 0) {
        $('#leaderboard-content').html('<div class="empty">No items match the selected filters.</div>');
        return;
    }

    const activeItemIds = activeItems.map(item => item.id.toString());

    // Filter models and calculate scores
    const modelScores = [];
    for (const model of rawData.models) {
        // Mode filter
        if (model.info.mode !== filterMode) continue;

        let totalScore = 0;
        let validItemsCount = 0;

        for (const id of activeItemIds) {
            if (model.results.hasOwnProperty(id)) {
                totalScore += model.results[id];
                validItemsCount++;
            }
        }

        const scorePercentage = validItemsCount > 0 ? (totalScore / validItemsCount) * 100 : 0;
        
        modelScores.push({
            model,
            scorePercentage,
            validItemsCount
        });
    }

    // Sort by score descending
    modelScores.sort((a, b) => b.scorePercentage - a.scorePercentage);

    if (modelScores.length === 0) {
        $('#leaderboard-content').html('<div class="empty">No models match the selected filters.</div>');
        return;
    }

    let rows = '';
    for (const entry of modelScores) {
        const info = entry.model.info;
        rows += `<tr>
            <td>${info.model_name || '—'}</td>
            <td>${info.model_size || '—'}</td>
            <td>${info.institution || '—'}</td>
            <td><strong>${entry.scorePercentage.toFixed(2)}%</strong></td>
        </tr>`;
    }

    const tableHtml = `
        <table>
            <thead>
                <tr>
                    <th>Model Name</th>
                    <th>Size</th>
                    <th>Institution</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;

    $('#leaderboard-content').html(tableHtml);
}
$(async () => {
    try {
        const user = await getMe();
        if (user) {
            renderHeaderStatus(user);
            renderRoleSwitcher(user.roles);
        }
    } catch (e) {
        // Not logged in, ignore
    }

    $('#filter-mode, #filter-tag, #filter-media, #filter-lang').on('change', renderTable);
    loadLeaderboard();
});
