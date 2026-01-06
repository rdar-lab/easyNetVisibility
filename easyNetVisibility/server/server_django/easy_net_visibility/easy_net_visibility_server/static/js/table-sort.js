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
            return acc + (parseInt(octet) || 0) * Math.pow(256, 3 - i);
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
                var diff = parseInt(aPart) - parseInt(bPart);
                if (diff !== 0) return diff;
            } else {
                if (aPart < bPart) return -1;
                if (aPart > bPart) return 1;
            }
        }
        return aParts.length - bParts.length;
    }

    // Parse date string "MM/DD/YYYY HH:MM:SS" to timestamp
    function parseDateTime(dateStr) {
        if (!dateStr) return 0;
        var match = dateStr.match(/(\d{2})\/(\d{2})\/(\d{4})\s+(\d{2}):(\d{2}):(\d{2})/);
        if (!match) return 0;
        var month = parseInt(match[1]) - 1;
        var day = parseInt(match[2]);
        var year = parseInt(match[3]);
        var hour = parseInt(match[4]);
        var minute = parseInt(match[5]);
        var second = parseInt(match[6]);
        return new Date(year, month, day, hour, minute, second).getTime();
    }

    function sortTable(table, columnIndex, ascending) {
        var tbody = $(table).find('tbody');
        var rows = tbody.find('tr').get();
        
        rows.sort(function(a, b) {
            var aVal = $(a).find('td').eq(columnIndex).text().trim();
            var bVal = $(b).find('td').eq(columnIndex).text().trim();
            
            // Check if column is IP (column 1)
            if (columnIndex === 1) {
                var aNum = ipToNumber(aVal);
                var bNum = ipToNumber(bVal);
                return ascending ? aNum - bNum : bNum - aNum;
            }
            
            // Check if column is date (columns 4, 5)
            if (columnIndex === 4 || columnIndex === 5) {
                var aTime = parseDateTime(aVal);
                var bTime = parseDateTime(bVal);
                return ascending ? aTime - bTime : bTime - aTime;
            }
            
            // Check if values are numeric (Open Ports column 6)
            if (columnIndex === 6) {
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
