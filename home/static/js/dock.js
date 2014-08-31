$(function () {
	// Dock initialize
	$('#dock').Fisheye(
		{
			maxWidth: 30,
			items: 'a',
			itemsText: 'span',
			container: '.dock-container',
			itemWidth: 60, /* 60 */
			proximity: 60, /* 60 */
			alignment : 'left', /* left */
			valign: 'bottom', /* top */
			halign : 'center' /* left */
		}
	);
});
