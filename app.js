async function loadData() {
    try {
        // Add a timestamp to bypass browser caching so we always get fresh data
        const response = await fetch('active_approvals.json?t=' + new Date().getTime());
        if (!response.ok) throw new Error("No data file found yet.");
        
        const data = await response.json();
        
        // Update timestamp
        const date = new Date(data.generated_at_utc);
        document.getElementById('last-updated').innerText = 
            `Last Scan: ${date.toLocaleString()} | Total Active: ${data.total_active}`;

        const tbody = document.getElementById('table-body');
        const emptyState = document.getElementById('empty-state');
        
        if (!data.approvals || data.approvals.length === 0) {
            emptyState.classList.remove('hidden');
            return;
        }

        // Build table rows
        tbody.innerHTML = data.approvals.map(item => {
            // Determine Risk Level
            let riskClass = 'risk-low';
            let riskLabel = 'Safe';
            
            if (item.spender_type === 'wallet' || item.spender_type === 'unknown') {
                riskClass = 'risk-high';
                riskLabel = 'High Risk';
            } else if (item.unlimited) {
                riskClass = 'risk-med';
                riskLabel = 'Warning';
            }

            // Format Allowance
            const allowanceText = item.unlimited ? 'UNLIMITED' : parseInt(item.allowance_raw).toLocaleString();
            const tokenSymbol = item.token_symbol || 'UNKNOWN';

            return `
                <tr class="border-b border-gray-800 transition-colors">
                    <td class="p-3 font-mono text-xs break-all text-blue-300">
                        <a href="https://tronscan.org/#/address/${item.owner}" target="_blank" class="hover:underline">${item.owner}</a>
                    </td>
                    <td class="p-3 font-mono text-xs break-all text-blue-300">
                        <a href="https://tronscan.org/#/address/${item.spender}" target="_blank" class="hover:underline">${item.spender}</a>
                    </td>
                    <td class="p-3">
                        <span class="${riskClass}">${item.spender_type.toUpperCase()}</span>
                    </td>
                    <td class="p-3 font-bold">${tokenSymbol}</td>
                    <td class="p-3 font-mono ${item.unlimited ? 'risk-med' : ''}">${allowanceText}</td>
                </tr>
            `;
        }).join('');

        // Add Search functionality
        document.getElementById('search').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#table-body tr');
            
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });

    } catch (error) {
        document.getElementById('last-updated').innerText = "Error loading data. Scanner might not have run yet.";
        document.getElementById('last-updated').classList.replace('text-blue-400', 'text-red-500');
    }
}

// Run when the page loads
document.addEventListener('DOMContentLoaded', loadData);
