/**
 * Simple table sorting functionality
 * Adds click handlers to table headers to sort table rows
 */
(function($) {
    'use strict';

    // IP address sorting comparison
    function ipToNumber(ip) {
        if (!ip) return 0;
        var parts = ip.split('.');
        if (parts.length !== 4) return 0;
        return parts.reduce(function(acc, octet, i) {
            return acc + (parseInt(octet, 10) || 0) * Math.pow(256, 3 - i);
        }, 0);
    }

    // Natural sort for strings with numbers
    function naturalSort(a, b) {
        var re = /(\d+)|(\D+)/g;
        var aParts = String(a).match(re) || [];
        var bParts = String(b).match(re) || [];
        
        for (var i = 0; i < Math.min(aParts.length, bParts.length); i++) {
            var aPart = aParts[i];
            var bPart = bParts[i];
            
            if (/^\d+$/.test(aPart) && /^\d+$/.test(bPart)) {
                var diff = parseInt(aPart, 10) - parseInt(bPart, 10);
                if (diff !== 0) return diff;
            } else {
                if (aPart < bPart) return -1;
                if (aPart > bPart) return 1;
            }
        }
        return aParts.length - bParts.length;
    }

    // Helper function to validate and create Date object
    function validateAndCreateDate(year, monthRaw, day, hour, minute, second) {
        // Basic range validation
        if (isNaN(monthRaw) || isNaN(day) || isNaN(year) ||
            isNaN(hour) || isNaN(minute) || isNaN(second)) {
            return 0;
        }

        if (monthRaw < 1 || monthRaw > 12) return 0;
        if (day < 1 || day > 31) return 0;
        if (hour < 0 || hour > 23) return 0;
        if (minute < 0 || minute > 59) return 0;
        if (second < 0 || second > 59) return 0;

        var monthIndex = monthRaw - 1;
        var d = new Date(year, monthIndex, day, hour, minute, second);

        // Ensure Date did not normalize an invalid value
        if (d.getFullYear() !== year ||
            d.getMonth() !== monthIndex ||
            d.getDate() !== day ||
            d.getHours() !== hour ||
            d.getMinutes() !== minute ||
            d.getSeconds() !== second) {
            return 0;
        }

        return d.getTime();
    }

    // Parse date string "MM/DD/YYYY HH:MM:SS" or "YYYY-MM-DD HH:MM:SS" to timestamp
    function parseDateTime(dateStr) {
        if (!dateStr) return 0;
        
        // Try ISO format first: YYYY-MM-DD HH:MM:SS
        var isoMatch = dateStr.match(/(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})/);
        if (isoMatch) {
            return validateAndCreateDate(
                parseInt(isoMatch[1], 10),  // year
                parseInt(isoMatch[2], 10),  // month
                parseInt(isoMatch[3], 10),  // day
                parseInt(isoMatch[4], 10),  // hour
                parseInt(isoMatch[5], 10),  // minute
                parseInt(isoMatch[6], 10)   // second
            );
        }
        
        // Try US format: MM/DD/YYYY HH:MM:SS
        var usMatch = dateStr.match(/(\d{2})\/(\d{2})\/(\d{4})\s+(\d{2}):(\d{2}):(\d{2})/);
        if (usMatch) {
            return validateAndCreateDate(
                parseInt(usMatch[3], 10),  // year
                parseInt(usMatch[1], 10),  // month
                parseInt(usMatch[2], 10),  // day
                parseInt(usMatch[4], 10),  // hour
                parseInt(usMatch[5], 10),  // minute
                parseInt(usMatch[6], 10)   // second
            );
        }
        
        return 0;
    }

    function sortTable(table, columnIndex, ascending) {
        var tbody = $(table).find('tbody');
        var rows = tbody.find('tr').get();
        
        // Get the sort type from the header
        var sortType = $(table).find('thead th').eq(columnIndex).attr('data-sort-type') || 'text';
        
        rows.sort(function(a, b) {
            var aVal = $(a).find('td').eq(columnIndex).text().trim();
            var bVal = $(b).find('td').eq(columnIndex).text().trim();
            
            // Sort based on the column's data-sort-type attribute
            if (sortType === 'ip') {
                var aNum = ipToNumber(aVal);
                var bNum = ipToNumber(bVal);
                return ascending ? aNum - bNum : bNum - aNum;
            }
            
            if (sortType === 'date') {
                var aTime = parseDateTime(aVal);
                var bTime = parseDateTime(bVal);
                return ascending ? aTime - bTime : bTime - aTime;
            }
            
            if (sortType === 'number') {
                var aNum = parseInt(aVal, 10) || 0;
                var bNum = parseInt(bVal, 10) || 0;
                return ascending ? aNum - bNum : bNum - aNum;
            }
            
            // Default: natural sort for strings
            var result = naturalSort(aVal, bVal);
            return ascending ? result : -result;
        });
        
        $.each(rows, function(index, row) {
            tbody.append(row);
        });
    }

    function initTableSort() {
        $('.sortable-table').each(function() {
            var table = this;
            
            $(table).find('thead th').each(function(index) {
                // Skip last column (action buttons)
                if (index === $(this).parent().children().length - 1) {
                    return;
                }
                
                $(this).css('cursor', 'pointer');
                $(this).attr('title', 'Click to sort');
                
                // Add sort indicator
                var indicator = $('<span class="sort-indicator"></span>');
                $(this).append(' ').append(indicator);
                
                $(this).on('click', function() {
                    var $this = $(this);
                    var currentOrder = $this.data('sort-order') || 'none';
                    var ascending = currentOrder !== 'asc';
                    
                    // Remove sort indicators from all headers
                    $(table).find('thead th').each(function() {
                        $(this).data('sort-order', 'none');
                        $(this).find('.sort-indicator').html('');
                    });
                    
                    // Set new sort order
                    $this.data('sort-order', ascending ? 'asc' : 'desc');
                    $this.find('.sort-indicator').html(ascending ? ' ▲' : ' ▼');
                    
                    sortTable(table, index, ascending);
                });
            });
        });
    }

    // Initialize when document is ready
    $(document).ready(function() {
        initTableSort();
    });

})(jQuery);
