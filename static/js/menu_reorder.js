    document.addEventListener('DOMContentLoaded', function() {
        const menuList = document.querySelector('.menu__inner');
        if (menuList) {
            // Get all list items (menu items)
            const menuItems = Array.from(menuList.children);

            // Define the desired order by name
            const desiredOrder = ["Home", "Lessons", "Categories", "Tags", "Search"];

            // Create a map for quick lookup of items by their text content
            const itemMap = new Map();
            menuItems.forEach(item => {
                const link = item.querySelector('a');
                if (link) {
                    itemMap.set(link.textContent.trim(), item);
                }
            });

            // Create a new ordered array of items
            const reorderedItems = [];
            desiredOrder.forEach(name => {
                if (itemMap.has(name)) {
                    reorderedItems.push(itemMap.get(name));
                }
            });

            // Clear the existing list and append reordered items
            menuList.innerHTML = ''; // Clear current items
            reorderedItems.forEach(item => {
                menuList.appendChild(item);
            });
        }
    });
    
