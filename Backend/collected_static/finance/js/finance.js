// Debug message to verify script is loading
console.log('Finance dashboard JavaScript loaded');

// Global state management
const selectedClaims = new Set();
let currentFilters = {};

// Report generation function
function generateReport() {
    if (selectedClaims.size === 0) {
        alert('Please select at least one claim');
        return;
    }
    // Always include special expenses and whiplash analysis
    const params = new URLSearchParams({
        claim_ids: Array.from(selectedClaims).join(','),
        include_special_expenses: 'on',
        include_whiplash: 'on'
    });
    window.location.href = `/finance/generate_report/?${params.toString()}`;
}

function openInvoiceModal() {
    if (selectedClaims.size === 0) {
        alert('Please select at least one claim');
        return;
    }
    const modal = document.getElementById('invoiceModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeInvoiceModal() {
    const modal = document.getElementById('invoiceModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Function to handle claim selection
function toggleClaimSelection(claimId) {
    console.log('Before toggle - Selected claims:', Array.from(selectedClaims));
    if (selectedClaims.has(claimId)) {
        selectedClaims.delete(claimId);
    } else {
        selectedClaims.add(claimId);
    }
    console.log('After toggle - Selected claims:', Array.from(selectedClaims));
    updateSelectedClaimsDisplay();
}

// Function to select all claims
function selectAllClaims() {
    console.log('Before select all - Selected claims:', Array.from(selectedClaims));
    const checkboxes = document.querySelectorAll('.claim-checkbox');
    checkboxes.forEach(checkbox => {
        const claimId = parseInt(checkbox.value);
        if (!selectedClaims.has(claimId)) {
            selectedClaims.add(claimId);
        }
        checkbox.checked = true;
    });
    console.log('After select all - Selected claims:', Array.from(selectedClaims));
    updateSelectedClaimsDisplay();
}

// Function to update the claims table with filtered results
function updateClaimsTable(claims) {
    console.log('Before table update - Selected claims:', Array.from(selectedClaims));
    const tbody = document.querySelector('.claims-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    claims.forEach(claim => {
        const row = document.createElement('tr');
        const isSelected = selectedClaims.has(claim.id);
        row.innerHTML = `
            <td>
                <input type="checkbox" class="claim-checkbox" value="${claim.id}" onchange="toggleClaimSelection(${claim.id})" ${isSelected ? 'checked' : ''}>
            </td>
            <td>${claim.id}</td>
            <td>${claim.accident_date}</td>
            <td>£${claim.settlement_value.toFixed(2)}</td>
            <td>${claim.whiplash ? 'Yes' : 'No'}</td>
            <td>£${claim.special_health_expenses.toFixed(2)}</td>
            <td>£${claim.special_reduction.toFixed(2)}</td>
        `;
        tbody.appendChild(row);
    });
    console.log('After table update - Selected claims:', Array.from(selectedClaims));
}

// Function to update the selected claims display
function updateSelectedClaimsDisplay() {
    const selectedSection = document.getElementById('selectedSection');
    const selectedClaimsDiv = document.getElementById('selectedClaims');
    if (!selectedSection || !selectedClaimsDiv) return;
    
    if (selectedClaims.size > 0) {
        selectedSection.style.display = 'block';
        selectedClaimsDiv.textContent = `Selected Claims: ${selectedClaims.size}`;
    } else {
        selectedSection.style.display = 'none';
    }
}

// Reset filters
function resetFilters() {
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.reset();
    }
    currentFilters = {};
    document.getElementById('resultsSection').style.display = 'none';
    updateSelectedClaimsDisplay();
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initial state:', Array.from(selectedClaims));
    
    // Initialize checkboxes for existing claims
    const initialCheckboxes = document.querySelectorAll('.claim-checkbox');
    initialCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            selectedClaims.add(parseInt(checkbox.value));
        }
    });
    console.log('After initial checkbox setup - Selected claims:', Array.from(selectedClaims));
    updateSelectedClaimsDisplay();

    // Filter form submission
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.onsubmit = function(e) {
            e.preventDefault();
            console.log('Before filter - Selected claims:', Array.from(selectedClaims));
            const formData = new FormData(this);
            currentFilters = Object.fromEntries(formData.entries());
            
            // Make AJAX call to filter endpoint
            fetch('/finance/filter_claims/?' + new URLSearchParams(currentFilters))
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(data => {
                            throw new Error(data.error || 'Server error occurred');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data || !data.claims) {
                        throw new Error('Invalid response format');
                    }
                    updateClaimsTable(data.claims);
                    document.getElementById('resultsSection').style.display = 'block';
                    console.log('After filter - Selected claims:', Array.from(selectedClaims));
                    updateSelectedClaimsDisplay();
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while filtering claims: ' + error.message);
                });
        };
    }

    // Invoice form submission
    const invoiceForm = document.getElementById('invoiceForm');
    if (invoiceForm) {
        invoiceForm.onsubmit = function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const params = new URLSearchParams(formData);
            params.append('claim_ids', Array.from(selectedClaims).join(','));
            window.location.href = `/finance/generate_invoice/?${params.toString()}`;
        };
    }
});

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
}; 