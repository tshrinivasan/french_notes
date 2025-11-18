    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        let searchIndex = [];

        // Fetch the search index
        fetch('/search.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                searchIndex = data;
                console.log("Search index loaded:", searchIndex.length, "items");
            })
            .catch(error => {
                console.error("Error loading search index:", error);
                if (searchResults) {
                    searchResults.innerHTML = '<p class="no-results">Error loading search functionality. Please try again later.</p>';
                }
            });

        if (searchInput) {
            searchInput.addEventListener('keyup', function(event) {
                const query = event.target.value.toLowerCase();
                if (searchResults) {
                    searchResults.innerHTML = ''; // Clear previous results
                }

                if (query.length < 2) { // Require at least 2 characters to search
                    return;
                }

                const filteredResults = searchIndex.filter(item =>
                    (item.title && item.title.toLowerCase().includes(query)) ||
                    (item.content && item.content.toLowerCase().includes(query)) ||
                    (item.tags && item.tags.some(tag => tag.toLowerCase().includes(query))) ||
                    (item.categories && item.categories.some(cat => cat.toLowerCase().includes(query)))
                );

                if (filteredResults.length > 0) {
                    filteredResults.forEach(item => {
                        const resultDiv = document.createElement('div');
                        resultDiv.classList.add('search-result-item');
                        resultDiv.innerHTML = `
                            <h3><a href="${item.uri}">${item.title}</a></h3>
                            <p>${item.content.substring(0, 200)}...</p>
                        `;
                        if (searchResults) {
                            searchResults.appendChild(resultDiv);
                        }
                    });
                } else {
                    if (searchResults) {
                        searchResults.innerHTML = '<p class="no-results">No results found.</p>';
                    }
                }
            });
        }
    });
    
