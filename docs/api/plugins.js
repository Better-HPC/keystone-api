/** Utility functions for customizing the appearance/behavior of swagger API documentation. */

/**
 * Disables the "Authorize" button in Swagger UI.
 *
 * This plugin overrides the `authorizeBtn` component with a null-rendering
 * function, effectively removing it from the UI.
 *
 * Example usage:
 *   window.ui = SwaggerUIBundle({
 *     url: '../openapi.yml',
 *     plugins: [disableAuthorizePlugin]
 *   });
 */
export function disableAuthorizePlugin() {
    return {
        wrapComponents: {
            authorizeBtn: () => () => null
        }
    }
}

/**
 * Returns the sortable index of a given tag based on a predefined ordering.
 * The ordering supports "startsWith" pattern matching so tags can be grouped
 * by prefix (e.g., "Auth" matches "Authentication", "AuthTokens", etc.).
 *
 * Example:
 *   desiredOrder = ["Auth", "User"]
 *   - All tags starting with "Auth" come first
 *   - All tags starting with "User" come next
 *   - Everything else is sorted alphabetically after
 */
export function createTagSorter(desiredOrder) {
    /**
     * Helper function to determine the order index for a given tag.
     * @param {string} tag - Tag name from the OpenAPI spec.
     * @returns {number} Sort priority index (lower = earlier).
     */
    function tagOrderIndex(tag) {
        for (let i = 0; i < desiredOrder.length; i++) {
            if (tag.startsWith(desiredOrder[i])) {
                return i;
            }
        }
        return desiredOrder.length; // Fallback for unmatched tags
    }

    /**
     * Comparator function passed to Swagger UI's `tagsSorter`.
     * Compares two tag names (a, b) based on our desired prefix order,
     * falling back to alphabetical sorting for ties.
     */
    return (a, b) => {
        const orderA = tagOrderIndex(a);
        const orderB = tagOrderIndex(b);

        // If both tags share the same order index, compare alphabetically
        if (orderA === orderB) {
            return a.localeCompare(b);
        }
        return orderA - orderB;
    };
}