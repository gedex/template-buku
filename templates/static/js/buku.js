!function($) {

	"use strict"; // jshint ;_;

	var $window = $(window);

	// Disable certain links in docs
  $('section [href^=#]').click(function (e) {
    e.preventDefault()
  })

	$('#hide-me').click(function() {
			$('#sidebar').addClass('hide');
			$('#book').addClass('full');
			$('#show-me-nav').addClass('shown');

			pinnedToggleNav();
	});

	$('#show-me-nav').click(function() {
		$('#book').removeClass('full');
		$('#sidebar').removeClass('hide');
		$('#show-me-nav').removeClass('shown');
	});

	$('#chapter-nav').affix({
		offset: {
			top: 10,
			bottom: 270
		}
	});

	$window.scroll(function() {
		pinnedToggleNav();
	});

	function pinnedToggleNav() {
		if ( $('#show-me-nav').hasClass('shown') ) {
			var winTop = $(window).scrollTop() - 1;

			$('#show-me-nav').css({top: winTop});
		}

		if ( $(window).width() > 767 ) {
			if ( $('#chapter-nav').hasClass('affix') || $('#chapter-nav').hasClass('affix-bottom') ) {
				$('#hide-me').css({top: 22});
			} else {
				$('#hide-me').css({top: 32});
			}
		}
	}

}(window.jQuery);