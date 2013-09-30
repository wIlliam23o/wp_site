/**
 * jQuery Banner Rotator 
 * Copyright (c) 2010-2013 Allan Ma (http://codecanyon.net/user/webtako)
 * Version: 2.1.5 (3/20/2013)
 */
;(function($) {
	var PREV = 0;
	var NEXT = 1;
	
	var iCount = 0;
	var ALIGN = {
		"TL":iCount++,
		"TC":iCount++,
		"TR":iCount++,
		"BL":iCount++,
		"BC":iCount++,
		"BR":iCount++,
		"LT":iCount++,
		"LC":iCount++,
		"LB":iCount++,
		"RT":iCount++,
		"RC":iCount++,
		"RB":iCount++
	};
	
	iCount = 0;
	var EFFECTS = {
		"block.top":iCount, 		'blockExpandDown':iCount++,		 
		"block.bottom":iCount, 		'blockExpandUp':iCount++,
		"block.left":iCount,		'blockExpandRight':iCount++,		
		"block.right":iCount,		'blockExpandLeft':iCount++, 
		"diag.fade":iCount,			'diagonalFade':iCount++,
		"diag.exp":iCount,			'diagonalExpand':iCount++,
		"rev.diag.fade":iCount,		'reverseDiagonalFade':iCount++,
		"rev.diag.exp":iCount,		'reverseDiagonalExpand':iCount++,
		"block.fade":iCount,		'blockRandomFade':iCount++,
		"block.exp":iCount,			'blockRandomExpand':iCount++,		
		"block.drop":iCount,		'blockRandomDrop':iCount++,		
		"block.top.zz":iCount,		'zigZagDown':iCount++,
		"block.bottom.zz":iCount,	'zigZagUp':iCount++,
		"block.left.zz":iCount,		'zigZagRight':iCount++,
		"block.right.zz":iCount,	'zigZagLeft':iCount++,
		"spiral.in":iCount,			'spiralIn':iCount++,
		"spiral.out":iCount,		'spiralOut':iCount++,
		"vert.tl":iCount,			'sliceDownRight':iCount++,
		"vert.tr":iCount,			'sliceDownLeft':iCount++,
		"vert.bl":iCount,			'sliceUpRight':iCount++,
		"vert.br":iCount,			'sliceUpLeft':iCount++,
		"fade.left":iCount,			'sliceFadeRight':iCount++,
		"fade.right":iCount,		'sliceFadeLeft':iCount++,
		"alt.left":iCount,			'sliceAltRight':iCount++,
		"alt.right":iCount,			'sliceAltLeft':iCount++,
		"blinds.left":iCount,		'blindsRight':iCount++,
		"blinds.right":iCount,		'blindsLeft':iCount++,
		"vert.random.fade":iCount,	'verticalSliceRandomFade':iCount++,		
		"horz.tl":iCount,			'sliceRightDown':iCount++,
		"horz.tr":iCount,			'sliceLeftDown':iCount++,
		"horz.bl":iCount,			'sliceRightUp':iCount++,
		"horz.br":iCount,			'sliceLeftUp':iCount++,
		"fade.top":iCount,			'sliceFadeDown':iCount++,
		"fade.bottom":iCount,		'sliceFadeUp':iCount++,
		"alt.top":iCount,			'sliceAltDown':iCount++,
		"alt.bottom":iCount,		'sliceAltUp':iCount++,
		"blinds.top":iCount, 		'blindsDown':iCount++,
		"blinds.bottom":iCount,		'blindsUp':iCount++,
		"horz.random.fade":iCount,	'horizontalSliceRandomFade':iCount++,
		"none":iCount++,
		"fade":iCount++,
		"crossFade":iCount++,
		"h.slide":iCount,			'horizontalSlide':iCount++,
		"v.slide":iCount,			'verticalSlide':iCount++,
		"random":iCount++
	};
	var NUM_EFFECTS = iCount;
	
	iCount = 0;
	var TEXT_EFFECTS = {
		"none":iCount++, 
		"fade":iCount++, 
		"down":iCount, 	"expandDown":iCount++, 
		"right":iCount, "expandRight":iCount++, 
		"up":iCount, 	"expandUp":iCount++, 
		"left":iCount, 	"expandLeft":iCount++, 
		"moveDown":iCount++, 
		"moveRight":iCount++, 
		"moveUp":iCount++, 
		"moveLeft":iCount++
	}
	
	var LIMIT = 250;
	var BLOCK_SIZE = 75;
	var SLICE_SIZE = 50;
	var DEFAULT_DELAY = 5000;
	var DURATION = 800;
	var ANIMATE_SPEED = 500;
	var SCROLL_RATE = 4;
	var SWIPE_MIN = 50;
	var UPDATE_LAYERS = "updateLayers";
	var RESET_LAYERS = "resetLayers";
	var UPDATE_LIST = "updatelist";
	var IS_MSIE = /MSIE (\d+\.\d+);/.test(navigator.userAgent);
	var MSIE7_BELOW = msieCheck(7);
	
	var CUBIC_BEZIER = new Array()
	CUBIC_BEZIER['linear'] = 'cubic-bezier(0.250, 0.250, 0.750, 0.750)';
	CUBIC_BEZIER[''] = CUBIC_BEZIER['swing'] = 'cubic-bezier(0.250, 0.100, 0.250, 1.000)';
	CUBIC_BEZIER['easeInQuad'] = 'cubic-bezier(0.550, 0.085, 0.680, 0.530)';
	CUBIC_BEZIER['easeOutQuad'] = 'cubic-bezier(0.250, 0.460, 0.450, 0.940)';
	CUBIC_BEZIER['easeInOutQuad'] = 'cubic-bezier(0.455, 0.030, 0.515, 0.955)';
	CUBIC_BEZIER['easeInCubic'] = 'cubic-bezier(0.550, 0.055, 0.675, 0.190)';
	CUBIC_BEZIER['easeOutCubic'] = 'cubic-bezier(0.215, 0.610, 0.355, 1.000)';
	CUBIC_BEZIER['easeInOutCubic'] = 'cubic-bezier(0.645, 0.045, 0.355, 1.000)';
	CUBIC_BEZIER['easeInQuart'] = 'cubic-bezier(0.895, 0.030, 0.685, 0.220)';
	CUBIC_BEZIER['easeOutQuart'] = 'cubic-bezier(0.165, 0.840, 0.440, 1.000)';
	CUBIC_BEZIER['easeInOutQuart'] = 'cubic-bezier(0.770, 0.000, 0.175, 1.000)';
	CUBIC_BEZIER['easeInQuint'] = 'cubic-bezier(0.755, 0.050, 0.855, 0.060)';
	CUBIC_BEZIER['easeOutQuint'] = 'cubic-bezier(0.230, 1.000, 0.320, 1.000)';
	CUBIC_BEZIER['easeInOutQuint'] = 'cubic-bezier(0.860, 0.000, 0.070, 1.000)';
	CUBIC_BEZIER['easeInSine'] = 'cubic-bezier(0.470, 0.000, 0.745, 0.715)';
	CUBIC_BEZIER['easeOutSine'] = 'cubic-bezier(0.390, 0.575, 0.565, 1.000)';
	CUBIC_BEZIER['easeInOutSine'] = 'cubic-bezier(0.445, 0.050, 0.550, 0.950)';
	CUBIC_BEZIER['easeInExpo'] = 'cubic-bezier(0.950, 0.050, 0.795, 0.035)';
	CUBIC_BEZIER['easeOutExpo'] = 'cubic-bezier(0.190, 1.000, 0.220, 1.000)';
	CUBIC_BEZIER['easeInOutExpo'] = 'cubic-bezier(1.000, 0.000, 0.000, 1.000)';
	CUBIC_BEZIER['easeInCirc'] = 'cubic-bezier(0.600, 0.040, 0.980, 0.335)';
	CUBIC_BEZIER['easeOutCirc'] = 'cubic-bezier(0.075, 0.820, 0.165, 1.000)';	
	CUBIC_BEZIER['easeInOutCirc'] = 'cubic-bezier(0.785, 0.135, 0.150, 0.860)';
	CUBIC_BEZIER['easeInBack'] = 'cubic-bezier(0.600, -0.280, 0.735, 0.045)';
	CUBIC_BEZIER['easeOutBack'] = 'cubic-bezier(0.175, 0.885, 0.320, 1.275)';
	CUBIC_BEZIER['easeInOutBack'] = 'cubic-bezier(0.680, -0.550, 0.265, 1.550)';
	
	var CSS_TRANSITION_END = {'transition':'transitionend',
						   	  'MozTransition':'transitionend',
						   	  'WebkitTransition':'webkitTransitionEnd'};
	
	var CSS_TRANSITIONS = {'transition':'transition',
						   'MozTransition':'-moz-transition',
						   'WebkitTransition':'-webkit-transition'};
						   
	var TRANSITION_STYLE = getStyleProperty('transition');
	
	var TRANSITION = "trsn";
	var RAND_TRANSITION = "randTrsn";
	var DIAG_TRANSITION = "diagTrsn";
	var ZIGZAG_TRANSITION = "zigzagTrsn";
	var DIR_TRANSITION = "dirTrsn";
	var SPIRAL_TRANSITION = "spiralTrsn";	
	var CLEAR_TRANSITION = "clearTrsn";
	
	//Vertical Stripes
	function VertStripes(rotator) {
		this._$stripes;
		this._arr;
		this._total;
		this._intervalId = null;
		this._rotator = rotator;
		this._areaWidth = rotator._screenWidth;
		this._areaHeight = rotator._screenHeight;
		this._size = rotator._vertSize;
		this._delay = rotator._vertDelay;
	
		this.init();
	}
	
	//init stripes
	VertStripes.prototype.init = function() {
		this._total = Math.ceil(this._areaWidth/this._size);
		if (this._total > LIMIT) {
			this._size = Math.ceil(this._areaWidth/LIMIT);
			this._total = Math.ceil(this._areaWidth/this._size);
		}
		var divs = "";
		for (var i = 0; i < this._total; i++) {
			divs += "<div class='vpiece' id='" + i + "' style='left:" + (i * this._size) + "px; height:" + this._areaHeight + "px'></div>";
		}					
		this._rotator.addToScreen(divs);
		
		this._$stripes = this._rotator._$screen.find("div.vpiece");
		this._arr = this._$stripes.toArray();
		
		if (false !== TRANSITION_STYLE && false !== this._rotator._cssTrsn) {
			$(this).bind(TRANSITION, this.cssAnimate)
			       .bind(RAND_TRANSITION, this.cssRandom)
				   .bind(CLEAR_TRANSITION, this.cssClear);
		}
		else {
			$(this).bind(TRANSITION, this.jsAnimate)
				   .bind(RAND_TRANSITION, this.jsRandom)
				   .bind(CLEAR_TRANSITION, this.jsClear);
		}
	}

	//clear animation
	VertStripes.prototype.clear = function() {
		$(this).trigger(CLEAR_TRANSITION);
	}
	
	//clear js animation
	VertStripes.prototype.jsClear = function() {
		clearInterval(this._intervalId);
		this._intervalId = null;
		this._$stripes.stop(true).css({"z-index":2, opacity:0});
	}
	
	//clear css animation
	VertStripes.prototype.cssClear = function() {
		this._$stripes.unbind(CSS_TRANSITION_END[TRANSITION_STYLE]).cssTransitionStop(false).css({"z-index":2, opacity:0, display:'none'});
	}
	
	//display content
	VertStripes.prototype.displayContent = function($img, effect, duration, easing) {
		this.setPieces($img, effect);
		if (effect == EFFECTS["verticalSliceRandomFade"]) {
			$(this).trigger(RAND_TRANSITION, [$img, duration, easing]);
		}
		else {
			this.animate($img, effect, duration, easing);
		}
	}			
	
	//set image stripes
	VertStripes.prototype.setPieces = function($img, effect) {
		switch (effect) {
			case EFFECTS["sliceDownRight"]:
			case EFFECTS["sliceDownLeft"]:
				this.setVertPieces($img, -this._areaHeight, 1, this._size, false);
				break;
			case EFFECTS["sliceUpRight"]:
			case EFFECTS["sliceUpLeft"]:
				this.setVertPieces($img, this._areaHeight, 1, this._size, false);
				break;
			case EFFECTS["sliceAltRight"]:
			case EFFECTS["sliceAltLeft"]:
				this.setVertPieces($img, 0, 1, this._size, true);
				break;
			case EFFECTS["blindsRight"]:
			case EFFECTS["blindsLeft"]:
				this.setVertPieces($img, 0, 1, 0, false);
				break;
			default:
				this.setVertPieces($img, 0, 0, this._size, false);
		}
	}
	
	//set vertical stripes
	VertStripes.prototype.setVertPieces = function($img, topPos, opacity, width, alt) {
		var imgSrc = $img.attr("src");
		var tOffset = 0;
		var lOffset = 0;
		if (this._rotator._autoCenter) {
			tOffset = (this._areaHeight - $img.height())/2;
			lOffset = (this._areaWidth - $img.width())/2;
		}
		
		for (var i = 0; i < this._total; i++) {
			var $strip = this._$stripes.eq(i);
			var xPos =  ((-i * this._size) + lOffset);
			if (alt) {
				topPos = (i%2) == 0 ? -this._areaHeight: this._areaHeight;
			}
			$strip.css({background:"url('"+ imgSrc +"') no-repeat", backgroundPosition:xPos + "px " + tOffset + "px", opacity:opacity, top:topPos, width:width, "z-index":3});
		}
	}
	
	//animate stripes			
	VertStripes.prototype.animate = function($img, effect, duration, easing) {
		var start, end, incr;
		switch (effect) {
			case EFFECTS["sliceDownRight"]:   case EFFECTS["sliceUpRight"]: 
			case EFFECTS["sliceFadeRight"]: case EFFECTS["blindsRight"]: 
			case EFFECTS["sliceAltRight"]:
				start = 0;
				end = this._total - 1;
				incr = 1;
				break;
			default:
				start = this._total - 1;
				end = 0;
				incr = -1;
		}
		
		$(this).trigger(TRANSITION, [$img, duration, easing, start, end, incr]);
	}
	
	//js animate
	VertStripes.prototype.jsAnimate = function(e, $img, duration, easing, start, end, incr) {
		var that = this;
		this._intervalId = setInterval(
			function() {
				that._$stripes.eq(start).animate({top:0, opacity:1, width:that._size}, duration, easing,
					function() {
						if ($(this).attr("id") == end) {
							that._rotator.showContent($img);
						}
					}
				);
				if (start == end) {
					clearInterval(that._intervalId);
					that._intervalId = null;
				}
				start += incr;
			}, this._delay);
	}
	
	//css animate
	VertStripes.prototype.cssAnimate = function(e, $img, duration, easing, start, end, incr) {
		var that = this;
		var currDelay = 0;
		
		this._$stripes.show();
		while(true) {
			this._$stripes.eq(start).cssTransition({top:0, opacity:1, width:this._size}, duration, easing, currDelay, 
				function() {  
					if ($(this).attr("id") == end)
						that._rotator.showContent($img);
				});
			
			if (start == end) {
				break;
			}
			
			start += incr;
			currDelay += this._delay;
		}
	}
	
	//js random effect
	VertStripes.prototype.jsRandom = function(e, $img, duration, easing) {
		var that = this;
		shuffleArray(this._arr);
		var i = 0;
		var count = 0;
		
		this._intervalId = setInterval(
			function() {
				$(that._arr[i++]).animate({opacity:1}, duration, easing,
						function() {
							if (++count == that._total) {
								that._rotator.showContent($img);
							}
						});
				if (i == that._total) {
					clearInterval(that._intervalId);
					that._intervalId = null;
				}
			}, this._delay);
	}
	
	//css random effect
	VertStripes.prototype.cssRandom = function(e, $img, duration, easing) {
		var that = this;
		var count = 0;
		shuffleArray(this._arr);
		
		this._$stripes.show();
		for (var i = 0; i <= this._total; i++) {
			$(this._arr[i]).cssTransition({opacity:1}, duration, easing, i * this._delay, 
						function() {
							if (++count == that._total)
								that._rotator.showContent($img);
						});	
		}
	}
	
	//Horizontal Stripes
	function HorzStripes(rotator) {
		this._$stripes;
		this._arr;
		this._total;
		this._intervalId = null;
		this._rotator = rotator;
		this._areaWidth = rotator._screenWidth;
		this._areaHeight = rotator._screenHeight;
		this._size = rotator._horzSize;
		this._delay = rotator._horzDelay;
		
		this.init();
	}
	
	//init stripes
	HorzStripes.prototype.init = function() {			
		this._total = Math.ceil(this._areaHeight/this._size);
		if (this._total > LIMIT) {
			this._size = Math.ceil(this._areaHeight/LIMIT);
			this._total = Math.ceil(this._areaHeight/this._size);
		}
		var divs = "";
		for (var i = 0; i < this._total; i++) {
			divs += "<div class='hpiece' id='" + i + "' style='top:" + (i * this._size) + "px; width:" + this._areaWidth + "px'><!-- --></div>";
		}				
		this._rotator.addToScreen(divs);
		
		this._$stripes = this._rotator._$screen.find("div.hpiece");
		this._arr = this._$stripes.toArray();
	
		if (false !== TRANSITION_STYLE && false !== this._rotator._cssTrsn) {
			$(this).bind(TRANSITION, this.cssAnimate)
				   .bind(RAND_TRANSITION, this.cssRandom)
				   .bind(CLEAR_TRANSITION, this.cssClear);
		}
		else {
			$(this).bind(TRANSITION, this.jsAnimate)
			       .bind(RAND_TRANSITION, this.jsRandom)
				   .bind(CLEAR_TRANSITION, this.jsClear);
		}
	}

	//clear animation
	HorzStripes.prototype.clear = function() {
		$(this).trigger(CLEAR_TRANSITION);
	}
	
	//clear js animation
	HorzStripes.prototype.jsClear = function() {
		clearInterval(this._intervalId);
		this._intervalId = null;
		this._$stripes.stop(true).css({"z-index":2, opacity:0});
	}
	
	//clear css animation
	HorzStripes.prototype.cssClear = function() {
		this._$stripes.unbind(CSS_TRANSITION_END[TRANSITION_STYLE]).cssTransitionStop(false).css({"z-index":2, opacity:0, display:'none'});
	}
	
	//display content
	HorzStripes.prototype.displayContent = function($img, effect, duration, easing) {
		this.setPieces($img, effect);
		if (effect == EFFECTS["horizontalSliceRandomFade"]) {
			$(this).trigger(RAND_TRANSITION, [$img, duration, easing]);
		}
		else {
			this.animate($img, effect, duration, easing);
		}
	}			
	
	//set image stripes
	HorzStripes.prototype.setPieces = function($img, effect) {
		switch (effect) {
			case EFFECTS["sliceLeftDown"]:
			case EFFECTS["sliceLeftUp"]:
				this.setHorzPieces($img, this._areaWidth, 1, this._size, false);
				break;
			case EFFECTS["sliceRightDown"]:
			case EFFECTS["sliceRightUp"]:
				this.setHorzPieces($img, -this._areaWidth, 1, this._size, false);
				break;
			case EFFECTS["sliceAltDown"]:
			case EFFECTS["sliceAltUp"]:
				this.setHorzPieces($img, 0, 1, this._size, true);
				break;
			case EFFECTS["blindsDown"]:
			case EFFECTS["blindsUp"]:
				this.setHorzPieces($img, 0, 1, 0, false);
				break;
			default:
				this.setHorzPieces($img, 0, 0, this._size, false);
		}
	}
	
	//set horizontal stripes
	HorzStripes.prototype.setHorzPieces = function($img, leftPos, opacity, height, alt) {
		var imgSrc = $img.attr("src");
		var tOffset = 0;
		var lOffset = 0;
		if (this._rotator._autoCenter) {
			tOffset = (this._areaHeight - $img.height())/2;
			lOffset = (this._areaWidth - $img.width())/2;
		}
		
		for (var i = 0; i < this._total; i++) {
			var $strip = this._$stripes.eq(i);
			var yPos = ((-i * this._size) + tOffset);
			if (alt) {
				leftPos = (i%2) == 0 ? -this._areaWidth: this._areaWidth;
			}
			$strip.css({background:"url('"+ imgSrc +"') no-repeat", backgroundPosition:lOffset + "px " + yPos + "px", opacity:opacity, left:leftPos, height:height, "z-index":3});  
		}
	}
	
	//animate stripes			
	HorzStripes.prototype.animate = function($img, effect, duration, easing) {
		var start, end, incr;
		switch (effect) {
			case EFFECTS["sliceRightDown"]:  case EFFECTS["sliceLeftDown"]: 
			case EFFECTS["sliceFadeDown"]: case EFFECTS["blindsDown"]: 
			case EFFECTS["sliceAltDown"]:
				start = 0;
				end = this._total - 1;
				incr = 1;
				break;
			default:
				start = this._total - 1;
				end = 0;
				incr = -1;
		}
		
		$(this).trigger(TRANSITION, [$img, duration, easing, start, end, incr]);
	}
	
	//js animate
	HorzStripes.prototype.jsAnimate = function(e, $img, duration, easing, start, end, incr) {
		var that = this;
		this._intervalId = setInterval(
			function() {
				that._$stripes.eq(start).animate({left:0, opacity:1, height:that._size}, duration, easing,
					function() {
						if ($(this).attr("id") == end) {
							that._rotator.showContent($img);
						}
					}
				);
				if (start == end) {
					clearInterval(that._intervalId);
					that._intervalId = null;
				}
				start += incr;
			}, this._delay);
	}
	
	//css animate
	HorzStripes.prototype.cssAnimate = function(e, $img, duration, easing, start, end, incr) {
		var that = this;
		var currDelay = 0;
		
		this._$stripes.show();
		while(true) {
			this._$stripes.eq(start).cssTransition({left:0, opacity:1, height:this._size}, duration, easing, currDelay, 
				function() {  
					if ($(this).attr("id") == end)
						that._rotator.showContent($img);
				});
			
			if (start == end) {
				break;
			}
			
			start += incr;
			currDelay += this._delay;
		}
	}
	
	//js random effect
	HorzStripes.prototype.jsRandom = function(e, $img, duration, easing) {
		var that = this;
		shuffleArray(this._arr);
		var i = 0;
		var count = 0;
		this._intervalId = setInterval(
			function() {
				$(that._arr[i++]).animate({opacity:1}, duration, easing,
						function() {
							if (++count == that._total) {
								that._rotator.showContent($img);
							}
						});
				if (i == that._total) {
					clearInterval(that._intervalId);
					that._intervalId = null;
				}
			}, this._delay);
	}
		
	//css random effect
	HorzStripes.prototype.cssRandom = function(e, $img, duration, easing) {		
		var that = this;
		var count = 0;
		shuffleArray(this._arr);
		
		this._$stripes.show();
		for (var i = 0; i <= this._total; i++) {
			$(this._arr[i]).cssTransition({opacity:1}, duration, easing, i * this._delay, 
						function() {
							if (++count == that._total)
								that._rotator.showContent($img);
						});	
		}
	}
	
	//class Blocks
	function Blocks(rotator) {
		this._$blockArr;
		this._$blocks;
		this._arr;
		this._numRows;
		this._numCols;
		this._total;
		this._intervalId;
		this._rotator = rotator;
		this._areaWidth = rotator._screenWidth;
		this._areaHeight = rotator._screenHeight;
		this._size = rotator._blockSize;
		this._delay = rotator._blockDelay;
	
		this.init();
	}
	
	//init blocks
	Blocks.prototype.init = function() {
		this._numRows = Math.ceil(this._areaHeight/this._size);
		this._numCols = Math.ceil(this._areaWidth/this._size);
		this._total = this._numRows * this._numCols;
		if (this._total > LIMIT) {
			this._size = Math.ceil(Math.sqrt((this._areaHeight * this._areaWidth)/LIMIT));
			this._numRows = Math.ceil(this._areaHeight/this._size);
			this._numCols = Math.ceil(this._areaWidth/this._size);
			this._total = this._numRows * this._numCols;
		}
		
		var divs = "";
		for (var i = 0; i < this._numRows; i++) {					
			for (var j = 0; j < this._numCols; j++) {
				divs += "<div class='block' id='" + i + "-" + j + "'></div>";
			}
		}
		this._rotator.addToScreen(divs);
		this._$blocks = this._rotator._$screen.find("div.block");
		this._$blocks.data({tlId:"0-0", trId:"0-"+(this._numCols - 1), blId:(this._numRows - 1)+"-0", brId:(this._numRows - 1)+"-"+(this._numCols - 1)});
		
		var k = 0;
		this._arr = this._$blocks.toArray();
		this._$blockArr = new Array(this._numRows);
		for (var i = 0; i < this._numRows; i++) {
			this._$blockArr[i] = new Array(this._numCols);
			for (var j = 0; j < this._numCols; j++) {
				this._$blockArr[i][j] = this._$blocks.filter("#" + (i + "-" + j)).data("top", i * this._size);
			}
		}
		
		if (false !== TRANSITION_STYLE && false !== this._rotator._cssTrsn) {
			$(this).bind(TRANSITION, this.cssAnimate)
				   .bind(DIAG_TRANSITION, this.cssDiagonal)
				   .bind(ZIGZAG_TRANSITION, this.cssZigZag)
				   .bind(DIR_TRANSITION, this.cssDirectional)
				   .bind(SPIRAL_TRANSITION, this.cssSpiral)
				   .bind(RAND_TRANSITION, this.cssRandom)
				   .bind(CLEAR_TRANSITION, this.cssClear);
		}
		else {
			$(this).bind(TRANSITION, this.jsAnimate)
			       .bind(DIAG_TRANSITION, this.jsDiagonal)
				   .bind(ZIGZAG_TRANSITION, this.jsZigZag)
				   .bind(DIR_TRANSITION, this.jsDirectional)
				   .bind(SPIRAL_TRANSITION, this.jsSpiral)
				   .bind(RAND_TRANSITION, this.jsRandom)
				   .bind(CLEAR_TRANSITION, this.jsClear);
		}
	}
	
	//clear blocks
	Blocks.prototype.clear = function() {
		$(this).trigger(CLEAR_TRANSITION);
	}
	
	//clear js transition
	Blocks.prototype.jsClear = function() {
		clearInterval(this._intervalId);
		this._intervalId = null;
		this._$blocks.stop(true).css({"z-index":2, opacity:0});
	}
	
	//clear css transition
	Blocks.prototype.cssClear = function() {
		this._$blocks.unbind(CSS_TRANSITION_END[TRANSITION_STYLE]).cssTransitionStop(false).css({"z-index":2, opacity:0, display:'none'});
	}
	
	//display content
	Blocks.prototype.displayContent = function($img, effect, duration, easing) {
		switch (effect) {
			case EFFECTS["diagonalFade"]:
				this.setBlocks($img, 0, this._size, 0);
				this.diagAnimate($img, {opacity:1}, false, duration, easing);
				break;
			case EFFECTS["diagonalExpand"]:
				this.setBlocks($img, 0, 0, 0);
				this.diagAnimate($img, {opacity:1, width:this._size, height:this._size}, false, duration, easing);
				break;
			case EFFECTS["reverseDiagonalFade"]:
				this.setBlocks($img, 0, this._size, 0);
				this.diagAnimate($img, {opacity:1}, true, duration, easing);
				break;
			case EFFECTS["reverseDiagonalExpand"]:
				this.setBlocks($img, 0, 0, 0);
				this.diagAnimate($img, {opacity:1, width:this._size, height:this._size}, true, duration, easing);
				break;
			case EFFECTS["blockRandomFade"]:
				this.setBlocks($img, 0, this._size, 0);
				$(this).trigger(RAND_TRANSITION, [$img, duration, easing]);
				break;
			case EFFECTS["blockRandomExpand"]:
				this.setBlocks($img, 1, 0, 0);
				$(this).trigger(RAND_TRANSITION, [$img, duration, easing]);
				break; 
			case EFFECTS["blockRandomDrop"]:
				this.setBlocks($img, 1, this._size, -(this._numRows * this._size));
				$(this).trigger(RAND_TRANSITION, [$img, duration, easing]);
				break;
			case EFFECTS["zigZagDown"]: 
			case EFFECTS["zigZagUp"]:
			case EFFECTS["zigZagRight"]: 
			case EFFECTS["zigZagLeft"]:
				this.setBlocks($img, 0, this._size, 0);
				this.zigZagAnimate($img, effect, duration, easing);
				break;
			case EFFECTS["spiralIn"]:
				this.setBlocks($img, 0, this._size, 0);
				this.spiralAnimate($img, false, duration, easing);
				break;
			case EFFECTS["spiralOut"]:
				this.setBlocks($img, 0, this._size, 0);
				this.spiralAnimate($img, true, duration, easing);
				break;
			default:
				this.setBlocks($img, 1, 0, 0);
				this.dirAnimate($img, effect, duration, easing);
		}
	}
	
	//set blocks 
	Blocks.prototype.setBlocks = function($img, opacity, size, tPos) {
		var tOffset = 0;
		var lOffset = 0;
		if (this._rotator._autoCenter) {
			tOffset = (this._areaHeight - $img.height())/2;
			lOffset = (this._areaWidth - $img.width())/2;
		}
		var imgSrc = $img.attr("src");
		for (var i = 0; i < this._numRows; i++) {							
			for (var j = 0; j < this._numCols; j++) {
				var tVal = ((-i * this._size) + tOffset);
				var lVal = ((-j * this._size) + lOffset);
				this._$blockArr[i][j].css({background:"url('"+ imgSrc +"') no-repeat", backgroundPosition:lVal + "px " + tVal + "px", 
										   opacity:opacity, top:(i * this._size) + tPos, left:(j * this._size), width:size, height:size, "z-index":3});
			}					
		}
	}
	
	//diagonal effect
	Blocks.prototype.diagAnimate = function($img, props, rev, duration, easing) {
		var $array = new Array(this._total);
		var start, end, incr, lastId;
		var diagSpan = (this._numRows - 1) + (this._numCols - 1);
		if (rev) {				
			start = diagSpan;
			end = -1;
			incr = -1;
			lastId = this._$blocks.data("tlId");
		}
		else {
			start = 0;
			end = diagSpan + 1;
			incr = 1;
			lastId = this._$blocks.data("brId");
		}
		
		var count = 0;
		while (start != end) {
			i = Math.min(this._numRows - 1, start);
			while(i >= 0) {			
				j = Math.abs(i - start);
				if (j >= this._numCols) {
					break;
				}
				$array[count++] = this._$blockArr[i][j];
				i--;
			}
			start+=incr;
		}
		
		$(this).trigger(DIAG_TRANSITION, [$img, props, duration, easing, $array, lastId]);
	}
	
	//js diagonal effect
	Blocks.prototype.jsDiagonal = function(e, $img, props, duration, easing, $array, lastId) {
		var that = this;
		var count = 0;
		
		this._intervalId = setInterval(
			function() {
				$array[count++].animate(props, duration, easing,
						function() {
							if ($(this).attr("id") == lastId) {
								that._rotator.showContent($img);
							}
						});
				
				if (count == that._total) {
					clearInterval(that._intervalId);
					that._intervalId = null;
				}			
			}, this._delay);
	}
	
	//css diagonal effect
	Blocks.prototype.cssDiagonal = function(e, $img, props, duration, easing, $array, lastId) {
		var that = this;
		
		this._$blocks.show();
		for (var i = 0; i < this._total; i++) {
			$array[i].cssTransition(props, duration, easing, i * this._delay, 
				function() {  
					if ($(this).attr("id") == lastId)
						that._rotator.showContent($img);
				});
		}
	}
	
	//zig zag effect
	Blocks.prototype.zigZagAnimate = function($img, effect, duration, easing) {
		var i = 0, j = 0, incr, lastId, horz;
		if (effect == EFFECTS["zigZagRight"]) {
			lastId = (this._numCols%2 == 0) ? this._$blocks.data("trId") : this._$blocks.data("brId");
			j = 0;
			incr = 1;
			horz = false;
		}
		else if (effect == EFFECTS["zigZagLeft"]) {
			lastId = (this._numCols%2 == 0) ? this._$blocks.data("tlId") : this._$blocks.data("blId");
			j = this._numCols - 1;
			incr = -1;
			horz = false;
		}
		else if (effect == EFFECTS["zigZagDown"]) {
			lastId = (this._numRows%2 == 0) ? this._$blocks.data("blId") : this._$blocks.data("brId");
			i = 0;
			incr = 1;
			horz = true;
		}
		else {
			lastId = (this._numRows%2 == 0) ? this._$blocks.data("tlId") : this._$blocks.data("trId");
			i = this._numRows - 1;
			incr = -1;
			horz = true;
		}
		
		$(this).trigger(ZIGZAG_TRANSITION, [$img, duration, easing, i, j, incr, lastId, horz]);
	}
	
	//js zig zag effect
	Blocks.prototype.jsZigZag = function(e, $img, duration, easing, i, j, incr, lastId, horz) {
		var that = this;
		var fwd = true;
		
		this._intervalId = setInterval(
			function() {
				that._$blockArr[i][j].animate({opacity:1}, duration, easing,
						function() {
							if ($(this).attr("id") == lastId) {
								that._rotator.showContent($img);
							}});
				
				if (that._$blockArr[i][j].attr("id") == lastId) {
					clearInterval(that._intervalId);
					that._intervalId = null;
				}
				
				if (horz) {
					(fwd ? j++ : j--);
					if (j == that._numCols || j < 0) {
						fwd = !fwd;
						j = (fwd ? 0 : that._numCols - 1);
						i+=incr;
					}						
				}
				else {
					(fwd ? i++ : i--);
					if (i == that._numRows || i < 0) {
						fwd = !fwd;
						i = (fwd ? 0 : that._numRows - 1);
						j+=incr;
					}
				}
			}, this._delay);
	}
	
	//css zig zag effect
	Blocks.prototype.cssZigZag = function(e, $img, duration, easing, i, j, incr, lastId, horz) {
		var that = this;
		var fwd = true;
		var currDelay = 0;
		
		this._$blocks.show();
		while(true) {
			this._$blockArr[i][j].cssTransition({opacity:1}, duration, easing, currDelay, 
				function() {  
					if ($(this).attr("id") == lastId) {
						that._rotator.showContent($img);
					}});
			
			if (this._$blockArr[i][j].attr("id") == lastId) {
				break;
			}
			
			if (horz) {
				(fwd ? j++ : j--);
				if (j == this._numCols || j < 0) {
					fwd = !fwd;
					j = (fwd ? 0 : this._numCols - 1);
					i+=incr;
				}						
			}
			else {
				(fwd ? i++ : i--);
				if (i == this._numRows || i < 0) {
					fwd = !fwd;
					i = (fwd ? 0 : this._numRows - 1);
					j+=incr;
				}
			}
			
			currDelay += this._delay;
		}
	}
	
	//direction effect
	Blocks.prototype.dirAnimate = function($img, effect, duration, easing) {
		var $array = new Array(this._total);
		var lastId;
		var count = 0;
		switch (effect) {
			case EFFECTS["blockExpandRight"]:
				lastId = this._$blocks.data("brId");
				for (var j = 0; j < this._numCols; j++) {
					for (var i = 0; i < this._numRows; i++) {
						$array[count++] = this._$blockArr[i][j];
					}
				}
				break;
			case EFFECTS["blockExpandLeft"]:
				lastId = this._$blocks.data("blId");
				for (var j = this._numCols - 1; j >= 0; j--) {
					for (var i = 0; i < this._numRows; i++) {
						$array[count++] = this._$blockArr[i][j];
					}
				}					
				break;
			case EFFECTS["blockExpandDown"]:
				lastId = this._$blocks.data("brId");
				for (var i = 0; i < this._numRows; i++) {
					for (var j = 0; j < this._numCols; j++) {
						$array[count++] = this._$blockArr[i][j];
					}
				}					
				break;
			default:
				lastId = this._$blocks.data("trId");
				for (var i = this._numRows - 1; i >= 0; i--) {
					for (var j = 0; j < this._numCols; j++) {
						$array[count++] = this._$blockArr[i][j];
					}
				}
		}
		
		$(this).trigger(DIR_TRANSITION, [$img, duration, easing, $array, lastId]);
	}
	
	//js direction effect
	Blocks.prototype.jsDirectional = function(e, $img, duration, easing, $array, lastId) {
		var that = this;
		var count = 0;
		
		this._intervalId = setInterval(
			function() {
				$array[count++].animate({width:that._size, height:that._size}, duration, easing,
						function() {
							if ($(this).attr("id") == lastId) {
								that._rotator.showContent($img);
							}
						});
				
				if (count == that._total) {
					clearInterval(that._intervalId);
					that._intervalId = null;
				}
			}, this._delay);
	}
	
	//css direction effect
	Blocks.prototype.cssDirectional = function(e, $img, duration, easing, $array, lastId) {
		var that = this;
		
		this._$blocks.show();
		for (var i = 0; i < this._total; i++) {
			$array[i].cssTransition({width:this._size, height:this._size}, duration, easing, i * this._delay, 
				function() {
					if ($(this).attr("id") == lastId) {
						that._rotator.showContent($img);
					}
				});
		}
	}
	
	//js random effect
	Blocks.prototype.jsRandom = function(e, $img, duration, easing) {
		var that = this;
		var i = 0, count = 0;
		
		shuffleArray(this._arr);
		this._intervalId = setInterval(
			function() {
				$(that._arr[i]).animate({top:$(that._arr[i]).data("top"), width:that._size, height:that._size, opacity:1}, duration, easing,
						function() {
							if (++count == that._total) {
								that._rotator.showContent($img);
							}
						});
				
				i++;
				if (i == that._total) {
					clearInterval(that._intervalId);
					that._intervalId = null;
				}
			}, this._delay);
	}
	
	//css random effect
	Blocks.prototype.cssRandom = function(e, $img, duration, easing) {
		var that = this;
		var count = 0;
		
		shuffleArray(this._arr);
		this._$blocks.show();
		for (var i = 0; i < this._total; i++) {
			$(this._arr[i]).cssTransition({top:$(this._arr[i]).data("top"), width:this._size, height:this._size, opacity:1}, duration, easing, i * this._delay,
				function() {
					if (++count == that._total) {
						that._rotator.showContent($img);
					}
				});
		}
	}
	
	//spiral effect
	Blocks.prototype.spiralAnimate = function($img, spiralOut, duration, easing) {			
		var i = 0, j = 0;
		var rowCount = this._numRows - 1;
		var colCount = this._numCols - 1;
		var dir = 0;
		var limit = colCount;
		var $array = new Array();
		while (rowCount >= 0 && colCount >=0) {
			var count = 0; 
			while(true) { 
				$array[$array.length] = this._$blockArr[i][j];
				if ((++count) > limit) {
					break;
				}
				switch(dir) {
					case 0:
						j++;
						break;
					case 1:
						i++;
						break;
					case 2:
						j--;
						break;
					case 3:
						i--;
				}
			} 
			switch(dir) {
				case 0:
					dir = 1;
					limit = (--rowCount);
					i++;
					break;
				case 1:
					dir = 2;
					limit = (--colCount);
					j--;
					break;
				case 2:
					dir = 3;
					limit = (--rowCount);
					i--;
					break;
				case 3:
					dir = 0;
					limit = (--colCount);
					j++;
			}
		}
		
		if ($array.length > 0) {
			if (spiralOut)
				$array.reverse();
			
			$(this).trigger(SPIRAL_TRANSITION, [$img, duration, easing, $array]);
		}
	}
	
	//js spiral effect
	Blocks.prototype.jsSpiral = function(e, $img, duration, easing, $array) {
		var end = $array.length - 1;
		var lastId = $array[end].attr("id");
		var k = 0;
		var that = this;
		
		this._intervalId = setInterval(
			function() {
				$array[k].animate({opacity:1}, duration, easing,
					function() {
						if ($(this).attr("id") == lastId) {
							that._rotator.showContent($img);
						}
					});
				if (k == end) {
					clearInterval(that._intervalId);
					that._intervalId = null;
				}	
				k++;
			}, this._delay);
	}

	//css spiral effect
	Blocks.prototype.cssSpiral = function(e, $img, duration, easing, $array) {
		var that = this;
		var end = $array.length - 1;
		var lastId = $array[end].attr("id");
		
		this._$blocks.show();
		for (var i = 0; i <= end; i++) {
			$array[i].cssTransition({opacity:1}, duration, easing, (i * this._delay), 
				function() {
					if ($(this).attr("id") == lastId) {
						that._rotator.showContent($img);
					}
				});
		}
	}

	//class Rotator
	function Rotator($obj, opts) {
		//set options
		this._screenWidth =  	isNaN(opts.width)  ? 'auto' : getPosNumber(opts.width, 825);
		this._screenHeight = 	isNaN(opts.height) ? 'auto' : getPosNumber(opts.height, 300);
		this._margin = 			getNonNegNumber(getDefinedVal(opts.button_margin, opts.margin), 4);
		this._globalEffect = 	getDefinedVal(opts.transition, opts.effect);
		this._duration = 		getPosNumber(getDefinedVal(opts.transition_speed, opts.duration), DURATION);
		this._globalDelay = 	getPosNumber(opts.delay, DEFAULT_DELAY);
		this._rotate = 			opts.auto_start;
		this._cpOutside = 		("undefined" != typeof opts.cpanel_position) ? ('outside' === opts.cpanel_position) : opts.outside_cpanel;
		this._cpAlign = 		opts.cpanel_align.toUpperCase();
		this._thumbWidth =		getPosNumber(opts.thumb_width, 24);
		this._thumbHeight = 	getPosNumber(opts.thumb_height, 24);
		this._buttonWidth =  	getPosNumber(opts.button_width, 24);
		this._buttonHeight =	getPosNumber(opts.button_height, 24);
		this._tooltipWidth = 	isNaN(opts.tooltip_width)  ? 'auto' : getPosNumber(opts.tooltip_width, 50);
		this._tooltipHeight = 	isNaN(opts.tooltip_height) ? 'auto' : getPosNumber(opts.tooltip_height, 50);
		this._bgImg =			opts.background_image;
		this._bgRepeat = 		opts.background_repeat;
		this._bgPosition = 		opts.background_position;
		this._displayPlayBtn =  opts.display_playbutton;
		this._displayTimer =	opts.display_timer;
		this._cpMouseover = 	window.Touch ? false : getDefinedVal(opts.cpanel_mouseover, opts.cpanel_onmouseover);
		this._textMousover = 	window.Touch ? false : getDefinedVal(opts.text_mouseover, opts.text_onmouseover);
		this._pauseMouseover = 	window.Touch ? false : getDefinedVal(opts.mouseover_pause, opts.pause_onmouseover);
		this._selectMouseover =	window.Touch ? false : getDefinedVal(opts.mouseover_select, opts.select_onmouseover);
		this._buttonsMouseover = window.Touch ? false : opts.dbuttons_onmouseover;
		this._tipType = 		getEnum(opts.tooltip_type, ['none', 'text', 'image'], 'none');
		this._tooltipDelay =	getNonNegNumber(opts.tooltip_delay, 0);
		this._textEffect = 		opts.text_effect;
		this._textDuration = 	getPosNumber(opts.text_duration, 500);
		this._textEasing =		opts.text_easing;
		this._textDelay =		getNonNegNumber(opts.text_delay, 0);
		this._textSync =		opts.text_sync;
		this._playOnce =		opts.play_once;
		this._autoCenter =		getDefinedVal(opts.auto_center, opts.center_image);
		this._easing =			opts.easing;
		this._timerAlign = 		opts.timer_align.toLowerCase();
		this._shuffle = 		opts.shuffle;
		this._mousewheelScroll = getDefinedVal(opts.mousewheel_scroll, opts.mousewheel);
		this._swipe =			opts.swipe;
		this._vertSize = 		getPosNumber(getDefinedVal(opts.vert_size, opts.vslice_size), SLICE_SIZE);
		this._horzSize = 		getPosNumber(getDefinedVal(opts.horz_size, opts.hslice_size), SLICE_SIZE);
		this._blockSize = 		getPosNumber(opts.block_size, BLOCK_SIZE);
		this._vertDelay = 		getPosNumber(getDefinedVal(opts.vstripe_delay, opts.vslice_delay), 75);
		this._horzDelay = 		getPosNumber(getDefinedVal(opts.hstripe_delay, opts.hslice_delay), 75);
		this._blockDelay = 		getPosNumber(opts.block_delay, 25);
		this._preload = 		opts.preload;
		this._cssTransition =	opts.css_transition;
		
		if ("undefined" != (typeof opts.display_thumbs)) {
			if (opts.display_thumbs) {
				if ("undefined" != (typeof opts.display_thumbimg) && opts.display_thumbimg)
					this._thumbType = 'image';
				else if ("undefined" != (typeof opts.display_numbers) && opts.display_numbers)
					this._thumbType = 'number';
				else
					this._thumbType = 'empty';
			}
			else
				this._thumbType = 'none';
		}
		else
			this._thumbType = getEnum(opts.thumb_type, ['none', 'empty', 'image', 'number', 'text'], 'none');
		
		if ("undefined" != (typeof opts.display_dbuttons)) {
			if (opts.display_dbuttons)
				this._dbuttonsType = ("undefined" != (typeof opts.display_side_buttons) && opts.display_side_buttons) ? 'large' : 'small';
			else
				this._dbuttonsType = 'none';
		}
		else
			this._dbuttonsType = getEnum(opts.dbuttons_type, ['none', 'large', 'small'], 'none');
			
		this._numItems;
		this._currIndex;
		this._prevIndex;
		this._delay;
		this._vStripes;
		this._hStripes;
		this._blocks;
		this._timerId;
		this._blockEffect;
		this._hStripeEffect;
		this._vStripeEffect;
		this._dir;
		this._cpVertical;
		this._zIndex;
		this._syncId;
		this._layerId;
		this._layerDelay;
		this._cssTrsnLayer;
		this._cssTrsn;
		this._slideTransition;
		this._verticalSlide;
		this._startX;
		this._startY;
		this._swipeDist;
		this._scrolling;
		
		this._$rotator;
		this._$screen;
		this._$strip;
		this._$mainLink;
		this._$layers;
		this._$preloader;
		this._$cpWrapper;
		this._$cpanel;
		this._$thumbPanel;
		this._$list;
		this._$thumbs;
		this._$buttonPanel;
		this._$playBtn;
		this._$sPrev;
		this._$sNext;
		this._$timer;
		this._$tooltip;
		this._$items;
		this._$contentBoxes;
		
		this._$rotator = this.getRotator($obj, "banner-rotator");
		
		if ("undefined" != typeof this._$rotator) {
			this.init();	
		}
		else {
			this._$rotator = this.getRotator($obj, "wt-rotator");
			if ("undefined" != typeof this._$rotator) {
				this._$rotator.removeClass("wt-rotator");
				
				if (!this._$rotator.hasClass("banner-rotator"))
					this._$rotator.addClass("banner-rotator");
				
				this.init();
			}
		}
	}	
	
	Rotator.prototype.getRotator = function($obj, className) {
		if ($obj.hasClass(className))
			return $obj;
		
		var $rotators = $obj.find("." + className);
		if (0 < $rotators.length)
			return $rotators.eq(0);
		
		return undefined;
	}
	
	//init rotator
	Rotator.prototype.init = function() {
		this._cssTrsnLayer = this._cssTrsn = (TRANSITION_STYLE && this._cssTransition);
		
		var $parent = this._$rotator.parent();
		if ('auto' === this._screenWidth) {
			var borderWidth = this._$rotator.outerWidth() - this._$rotator.width();
			this._screenWidth =  (0 < $parent.length && 0 < $parent.width()) ? ($parent.width() - borderWidth) : 825;
		}
		
		if ('auto' === this._screenHeight) {
			var borderHeight = this._$rotator.outerHeight() - this._$rotator.height();
			this._screenHeight = (0 < $parent.length && 0 < $parent.height()) ? ($parent.height() - borderHeight) : 300;
		}
		
		this._$screen = this._$rotator.find(">div.screen");
		if (0 == this._$screen.length) {
			this._$rotator.append("<div class='screen'></div>");
			this._$screen = this._$rotator.find(">div.screen");
		}
		
		this._$list = this._$rotator.find(">ul");
		if (0 < this._$list.length) {
			this._$list.wrap("<div class='c-panel'><div class='thumbnails'></div></div>");
		}
		
		this._$cpanel = this._$rotator.find(">div.c-panel");
		this._$buttonPanel = this._$cpanel.find(">div.buttons");
		if (0 == this._$buttonPanel.length) {
			this._$cpanel.append("<div class='buttons'><div class='prev-btn'></div><div class='play-btn'></div><div class='next-btn'></div></div>");
			this._$buttonPanel = this._$cpanel.find(">div.buttons");
		}
		
		this._$thumbPanel = this._$cpanel.find(">div.thumbnails");
		this._$list = this._$thumbPanel.find(">ul");
		this._$thumbs 	= this._$list.find(">li");
		
		this._timerId = this._syncId = this._layerId = null;
		this._currIndex = 0;
		this._prevIndex = -1;
		this._numItems = this._$thumbs.length;
		this._$items = new Array(this._numItems);
		this._blockEffect = this._hStripeEffect = this._vStripeEffect = false;
		this.checkEffect(EFFECTS[this._globalEffect]);
		this._slideTransition = (EFFECTS[this._globalEffect] === EFFECTS["horizontalSlide"] || EFFECTS[this._globalEffect] === EFFECTS["verticalSlide"]);
		this._cpVertical = ALIGN[this._cpAlign] >= ALIGN["LT"] ? true : false;
		
		if (this._numItems <= 1) {
			this._rotate = this._displayPlayBtn = this._displayTimer = this._mousewheelScroll = this._pauseMouseover = false;
			this._dbuttonsType = 'none';
		}
		
		if (this._shuffle) {
			this.shuffleItems();
		}
		
		this._$rotator.css({width:this._screenWidth, height:this._screenHeight});
		//init components
		this.initScreen();
		this.initButtons();
		this.initItems();
		
		if ('large' == this._dbuttonsType) {
			this._zIndex++;
			this._$sPrev.css("z-index", this._zIndex);
			this._$sNext.css("z-index", this._zIndex);
		}
		
		this.initCPanel();
		this.initTimerBar();
		
		if (this._textMousover) {
			if (false !== TRANSITION_STYLE && false !== this._cssTrsnLayer) {
				this._$rotator.bind("mouseenter", {elem:this}, this.displayCssLayers)
							  .bind("mouseleave", {elem:this}, this.hideLayers)
							  .bind(RESET_LAYERS, {elem:this}, this.resetCssLayers);
			}
			else {
				this._$rotator.bind("mouseenter", {elem:this}, this.displayLayers)
							  .bind("mouseleave", {elem:this}, this.hideLayers)
							  .bind(RESET_LAYERS, {elem:this}, this.resetLayers);
			}
		}
		else {
			if (false !== TRANSITION_STYLE && false !== this._cssTrsnLayer) {
				this._$rotator.bind(UPDATE_LAYERS, {elem:this}, this.updateCssLayers).bind(RESET_LAYERS,  {elem:this}, this.resetCssLayers);
			}
			else {
				this._$rotator.bind(UPDATE_LAYERS, {elem:this}, this.updateLayers).bind(RESET_LAYERS,  {elem:this}, this.resetLayers);
			}
		}
		
		//init transition components
		if (this._vStripeEffect) {
			this._vStripes = new VertStripes(this);
		}
		if (this._hStripeEffect) {
			this._hStripes = new HorzStripes(this);
		}
		if (this._blockEffect) {
			this._blocks = new Blocks(this);
		}
		
		if (window.Touch) {
			if (this._swipe) {
				this._startX = this._startY = this._swipeDist = null;
				this._verticalSlide = (EFFECTS[this._globalEffect] == EFFECTS["verticalSlide"]);
				this._$rotator.bind("touchstart", {elem:this}, this.touchStart);
			}
		}
		else if (this._mousewheelScroll) {
			this._$rotator.bind("mousewheel", {elem:this}, this.mouseScrollContent).bind("DOMMouseScroll", {elem:this}, this.mouseScrollContent);
		}	
		
		//init image loading
		if (!msieCheck(6) && this._preload)
			this.loadImg(0);
		else 
			this.loadAll();
			
		//display initial image
		if (this._$items.length > 0) { 
			this.loadContent(this._currIndex);
		}
	}
	
	Rotator.prototype.touchStart = function(e) {
		if (1 === e.originalEvent.touches.length) {
			var that = e.data.elem;
			that._startX = e.originalEvent.touches[0].pageX;
			that._startY = e.originalEvent.touches[0].pageY;		
			that._$rotator.bind("touchmove", {elem:that}, that.touchMove).one("touchend", {elem:that}, that.touchEnd);
		}
	}
	
	Rotator.prototype.touchMove = function(e) {
		var that = e.data.elem;
		var xDist = that._startX - e.originalEvent.touches[0].pageX;
		var	yDist = that._startY - e.originalEvent.touches[0].pageY;
			
		if (that._verticalSlide) {
			that._swipeDist = yDist;
			that._scrolling = Math.abs(that._swipeDist) < Math.abs(xDist);
		}
		else {
			that._swipeDist = xDist;
			that._scrolling = Math.abs(that._swipeDist) < Math.abs(yDist);
		}
		
		if (!that._scrolling)
			e.preventDefault();
	}
	
	Rotator.prototype.touchEnd = function(e) {
		var that = e.data.elem;
		that._$rotator.unbind("touchmove");
		
		if (!that._scrolling) {
			if (null !== that._swipeDist && Math.abs(that._swipeDist) > SWIPE_MIN) {
				if (that._swipeDist > 0)
					that.nextImg();
				else
					that.prevImg();
			}
		}
	
		that._startX = that._startY = that._swipeDist = null;
	}
	
	//add to screen
	Rotator.prototype.addToScreen = function(content) {
		this._$mainLink.append(content);
	}
	
	//init screen
	Rotator.prototype.initScreen = function() {
		var content = "<div class='preloader'></div><div class='timer'></div>";
		var numLayers = this.getMaxLayers();
		for (var i = 0; i < numLayers; i++) {
			content += "<div class='desc'><div class='inner-bg'></div><div class='inner-text'></div></div>";
		}
				
		this._$screen.append(content);
		this._$layers 	= this._$screen.find(">div.desc");
		this._$preloader 	= this._$screen.find(">div.preloader");
		this._$screen.css({width:this._screenWidth, height:this._screenHeight});
		if ("" != this._bgImg) {
			this._$screen.css({'background-image':'url(' + this._bgImg + ')', 'background-repeat':this._bgRepeat, 'background-position':this._bgPosition});
		}		
		this._$strip = $("<div class='strip'></div>");
		if (EFFECTS[this._globalEffect] == EFFECTS["horizontalSlide"]) {
			this._$screen.append(this._$strip);
			this._$strip.css({width:2*this._screenWidth, height:this._screenHeight});
			this._$thumbs.removeAttr("effect");
		}
		else if (EFFECTS[this._globalEffect] == EFFECTS["verticalSlide"]){
			this._$screen.append(this._$strip);
			this._$strip.css({width:this._screenWidth, height:2*this._screenHeight});
			this._$thumbs.removeAttr("effect");
		}
		else {
			this._$screen.append("<a href='#'></a>");
			this._$mainLink = this._$screen.find(">a:first");
		}
		
		content = "";
		if (this._slideTransition) {
			for (var i = 0; i < this._numItems; i++) {
				content += "<div class='content-box'><img class='main-img'/></div>";
			}
			this._$strip.append(content);
			this._$contentBoxes = this._$strip.find(">div.content-box");
			this._$contentBoxes.css({width:this._screenWidth, height:this._screenHeight});
		}
		else {
			for (var i = 0; i < this._numItems; i++) {
				content += "<img class='main-img'/>";
			}
			this._$mainLink.append(content);
		}
	}
	
	//init control panel
	Rotator.prototype.initCPanel = function() {
		if ('none' != this._thumbType || 'small' == this._dbuttonsType || this._displayPlayBtn) {
			if (!this._cpOutside) {
				this._$cpanel.css("z-index", ++this._zIndex);
				
				switch (ALIGN[this._cpAlign]) {
					case ALIGN["BL"]:								
						this.setHPanel("left");
						this.setInsideHP("bottom");
						break;
					case ALIGN["BC"]:
						this.setHPanel("center");
						this.setInsideHP("bottom");
						break;
					case ALIGN["BR"]:
						this.setHPanel("right");
						this.setInsideHP("bottom");
						break;
					case ALIGN["TL"]:								
						this.setHPanel("left");
						this.setInsideHP("top");
						break;
					case ALIGN["TC"]:								
						this.setHPanel("center");
						this.setInsideHP("top");
						break;
					case ALIGN["TR"]:								
						this.setHPanel("right");
						this.setInsideHP("top");
						break;
					case ALIGN["LT"]:
						this.setVPanel("top");
						this.setInsideVP("left");
						break;
					case ALIGN["LC"]:
						this.setVPanel("center");
						this.setInsideVP("left");
						break;
					case ALIGN["LB"]:
						this.setVPanel("bottom");
						this.setInsideVP("left");
						break;
					case ALIGN["RT"]:								
						this.setVPanel("top");
						this.setInsideVP("right");
						break;
					case ALIGN["RC"]:								
						this.setVPanel("center");
						this.setInsideVP("right");
						break;
					case ALIGN["RB"]:								
						this.setVPanel("bottom");
						this.setInsideVP("right");
						break;
				}
				
				if (this._cpMouseover) {
					var dir = this._cpVertical ? "left" : "top";
					this._$rotator.bind("mouseenter", {elem:this, dir:dir}, this.displayCPanel).bind("mouseleave", {elem:this, dir:dir}, this.hideCPanel);
				}
			}
			else {
				switch (ALIGN[this._cpAlign]) {
					case ALIGN["BL"]:
						this.setHPanel("left");
						this.setOutsideHP(false);
						break;
					case ALIGN["BC"]:
						this.setHPanel("center");
						this.setOutsideHP(false);
						break;
					case ALIGN["BR"]:
						this.setHPanel("right");
						this.setOutsideHP(false);
						break;
					case ALIGN["TL"]:
						this.setHPanel("left");
						this.setOutsideHP(true);
						break;
					case ALIGN["TC"]:							
						this.setHPanel("center");
						this.setOutsideHP(true);
						break;
					case ALIGN["TR"]:
						this.setHPanel("right");
						this.setOutsideHP(true);
						break;
					case ALIGN["LT"]:
						this.setVPanel("top");
						this.setOutsideVP(true);
						break;
					case ALIGN["LC"]:
						this.setVPanel("center");
						this.setOutsideVP(true);
						break;
					case ALIGN["LB"]:								
						this.setVPanel("bottom");
						this.setOutsideVP(true);
						break;
					case ALIGN["RT"]:								
						this.setVPanel("top");
						this.setOutsideVP(false);
						break;
					case ALIGN["RC"]:								
						this.setVPanel("center");
						this.setOutsideVP(false);
						break;
					case ALIGN["RB"]:
						this.setVPanel("bottom");
						this.setOutsideVP(false);
						break;
				}
			}
			this._$cpanel.css("visibility", "visible").click(preventDefault);
		}
	}
	
	//set control panel attributes
	Rotator.prototype.setHPanel = function(align) {
		this._$cpanel.css({"margin-top":this._margin, "margin-bottom":this._margin, height:Math.max(this._$thumbPanel.outerHeight(true), this._$buttonPanel.outerHeight(true))});
		var alignPos;
		if (align == "center") {
			alignPos = Math.round((this._screenWidth - this._$cpanel.width() - this._margin)/2);
		}
		else if (align == "left") {
			alignPos = this._margin;
		}
		else {
			alignPos = this._screenWidth - this._$cpanel.width();
		}
		this._$cpanel.css("left", alignPos);
	}
	
	Rotator.prototype.setVPanel = function(align) {
		this._$cpanel.css({"margin-left":this._margin, "margin-right":this._margin, width:Math.max(this._$thumbPanel.outerWidth(true), this._$buttonPanel.outerWidth(true))});
		var alignPos;
		if (align == "center") {
			alignPos = Math.round((this._screenHeight - this._$cpanel.height() - this._margin)/2);
		}
		else if (align == "top") {
			alignPos = this._margin;
		}
		else {
			alignPos = this._screenHeight - this._$cpanel.height();
		}
		this._$cpanel.css("top", alignPos);
	}
	
	Rotator.prototype.setInsideHP = function(align) {
		var offset, alignPos;
		if (align == "top") {
			alignPos = 0;
			offset = -this._$cpanel.outerHeight(true);
		}
		else {
			alignPos = this._screenHeight - this._$cpanel.outerHeight(true);
			offset = this._screenHeight;
		}
		this._$cpanel.data({offset:offset, pos:alignPos}).css({top: (this._cpMouseover ? offset : alignPos)});
	}
	
	Rotator.prototype.setInsideVP = function(align) {
		var offset, alignPos;
		if (align == "left") {
			alignPos = 0;
			offset = -this._$cpanel.outerWidth(true);
		}
		else {
			alignPos = this._screenWidth - this._$cpanel.outerWidth(true);
			offset = this._screenWidth;
		}
		this._$cpanel.data({offset:offset, pos:alignPos}).css({left:(this._cpMouseover ? offset : alignPos)});
	}
	
	Rotator.prototype.setOutsideHP = function(top) {
		this._$cpanel.wrap("<div class='outer-hp'></div>");
		this._$cpWrapper = this._$rotator.find(".outer-hp");
		this._$cpWrapper.height(this._$cpanel.outerHeight(true));
					
		if (top) {
			this._$cpWrapper.css({"border-top":"none", top:0});
			this._$screen.css("top", this._$cpWrapper.outerHeight());
		}
		else {
			this._$cpWrapper.css({"border-bottom":"none", top:this._screenHeight});
			this._$screen.css("top", 0);
		}
		this._$rotator.css({height:this._screenHeight + this._$cpWrapper.outerHeight()});
	}
	
	Rotator.prototype.setOutsideVP = function(left) {
		this._$cpanel.wrap("<div class='outer-vp'></div>");
		this._$cpWrapper = this._$rotator.find(".outer-vp");
		this._$cpWrapper.width(this._$cpanel.outerWidth(true));
		
		if (left) {
			this._$cpWrapper.css({"border-left":"none", left:0});
			this._$screen.css("left", this._$cpWrapper.outerWidth());
		}
		else {
			this._$cpWrapper.css({"border-right":"none", left:this._screenWidth});
			this._$screen.css("left", 0);
		}
		this._$rotator.css({width:this._screenWidth + this._$cpWrapper.outerWidth()});
	}
	
	//init buttons
	Rotator.prototype.initButtons = function() {
		this._$playBtn 	= this._$buttonPanel.find("div.play-btn");
		var $prevBtn = this._$buttonPanel.find("div.prev-btn");
		var $nextBtn = this._$buttonPanel.find("div.next-btn");
	
		//config directional buttons
		if ('small' == this._dbuttonsType) {
			$prevBtn.bind("click", {elem:this}, this.prevImg);
			$nextBtn.bind("click", {elem:this}, this.nextImg);
		}
		else {
			$prevBtn.hide();
			$nextBtn.hide();
		}
		
		//config play button
		if (this._displayPlayBtn) {
			this._$playBtn.toggleClass("pause", this._rotate).bind("click", {elem:this}, this.togglePlay);
		}
		else {
			this._$playBtn.hide();
		}
		
		if (this._pauseMouseover) {
			this._$rotator.bind("mouseenter", {elem:this}, this.pause).bind("mouseleave", {elem:this}, this.play);
		}
		
		if ('large' == this._dbuttonsType) {
			this._$screen.append("<div class='s-prev'></div><div class='s-next'></div>");
			this._$sPrev = this._$screen.find(".s-prev");
			this._$sNext = this._$screen.find(".s-next");
			this._$sPrev.bind("click", {elem:this}, this.prevImg).mousedown(preventDefault);
			this._$sNext.bind("click", {elem:this}, this.nextImg).mousedown(preventDefault);
			
			if (this._buttonsMouseover) {
				this._$sPrev.css("left",-this._$sPrev.width());
				this._$sNext.css("margin-left",0);
				this._$rotator.bind("mouseenter", {elem:this}, this.showSideButtons).bind("mouseleave", {elem:this}, this.hideSideButtons);
			}
		}
		
		var $buttons = this._$buttonPanel.find(">div").css({width:this._buttonWidth, height:this._buttonHeight}).mousedown(preventDefault);
		if (this._cpVertical) {
			$prevBtn.addClass("up");
			$nextBtn.addClass("down");
			$buttons.css("margin-bottom", this._margin);   
			this._$buttonPanel.width($buttons.outerWidth());
			if (MSIE7_BELOW) {
				this._$buttonPanel.height(this._$buttonPanel.find(">div:visible").length * $buttons.outerHeight(true));
			}
			if ('none' != this._thumbType && this._thumbWidth > this._buttonWidth) {
				var m = this._thumbWidth - this._buttonWidth;
				switch (ALIGN[this._cpAlign]) {
					case ALIGN["RT"]: case ALIGN["RC"]: case ALIGN["RB"]:
						this._$buttonPanel.css("margin-left", m);
						break;
					default:
						this._$buttonPanel.css("margin-right", m);
				}
			}
		}
		else {
			$buttons.css("margin-right", this._margin);
			this._$buttonPanel.height($buttons.outerHeight());
			if (MSIE7_BELOW) {
				this._$buttonPanel.width(this._$buttonPanel.find(">div:visible").length * $buttons.outerWidth(true));
			}
			if ('none' != this._thumbType && this._thumbHeight > this._buttonHeight) {
				var m = this._thumbHeight - this._buttonHeight;
				switch (ALIGN[this._cpAlign]) {
					case ALIGN["TL"]: case ALIGN["TC"]: case ALIGN["TR"]:
						this._$buttonPanel.css("margin-bottom", m);
						break;
					default:
						this._$buttonPanel.css("margin-top", m);
				}
			}
		}
	}			
	
	//init timer bar
	Rotator.prototype.initTimerBar = function() {
		this._$timer = this._$screen.find(".timer").data("pct", 1);
		if (this._displayTimer) {
			this._$timer.css("visibility", "visible");
			this._$timer.css("top", this._timerAlign == "top" ? 0 : this._screenHeight - this._$timer.height());
		}
		else {
			this._$timer.hide();
		}
	}
	
	//init items
	Rotator.prototype.initItems = function() {
		var that = this;
		
		var minLayerZIndex = parseInt(this._$layers.css("z-index"));
		this._zIndex = minLayerZIndex;
		for (var i = 0; i < this._numItems; i++) {
			var $thumb = this._$thumbs.eq(i);
			
			var $imgLink = $thumb.find(">a").eq(0);
			var imgUrl  = getDefinedVal($imgLink.attr("href"), '');
			var caption = getDefinedVal($imgLink.attr("title"), '');
			
			var $link = $thumb.find(">a").eq(1);
			var href   = getDefinedVal($link.attr("href"), '');
			var target = getDefinedVal($link.attr("target"), '');
			
			var itemEffect = EFFECTS[$thumb.attr("data-effect")];
			if ((typeof itemEffect == "undefined") || itemEffect ==  EFFECTS["horizontalSlide"] || itemEffect ==  EFFECTS["verticalSlide"]) {
				itemEffect = EFFECTS[this._globalEffect];
			}
			else {
				this.checkEffect(itemEffect);
			}
			
			var itemDuration = getPosNumber($thumb.attr("data-duration"), this._duration);
			var itemEasing =   getDefinedVal($thumb.attr("data-easing"), this._easing);
			var itemDelay =    getPosNumber($thumb.attr("data-delay"), this._globalDelay);
			
			if (endsWith(itemEasing, 'Elastic') || endsWith(itemEasing, 'Bounce'))
				this._cssTrsn = false;
				
			$thumb.data({imgurl:imgUrl, caption:caption, ttText:$thumb.find(">.tt-text").html(), href:href, target:target, effect:itemEffect, duration:itemDuration, easing:itemEasing, delay:itemDelay, complete:false});
			this.initLayerData($thumb, minLayerZIndex);
			this._$items[i] = $thumb;
			
			if ("number" == this._thumbType) {
				$thumb.append(i+1);
			}
			else if ("text" == this._thumbType) {
				$thumb.append($thumb.data("caption"));
			}
			
			var $img;
			if (this._slideTransition) {
				$img = this._$contentBoxes.eq(i).find(">img.main-img");
			}
			else {
				$img = this._$mainLink.find(">img.main-img").eq(i);
			}
			$thumb.data({img:$img});
		}
		
		this._$layers.find(">div.inner-text").css({width:"auto", height:"auto"}).html("");
		this._$layers.css({visibility:"visible", display:"none"});
		
		if ('none' == this._thumbType) {
			this._$thumbs.hide();
		}
		else {
			if ("image" == this._thumbType) {
				this._$thumbs.addClass("image").each(function(n) {
					var $imgLink = $(this).find(">a").eq(0).removeAttr("title");
					var $img = $imgLink.find(">img");
					if (0 < $img.length) {
						$img.removeAttr("alt");			
						$img.one("load", function() {
							that.maximizeImage($(this), that._thumbWidth, that._thumbHeight);
						});
					
						if ($img[0].complete || "complete" == $img[0].readyState )
							$img.trigger("load");
					}		
				});
			}
			
			this._$thumbs.css({width:this._thumbWidth, height:this._thumbHeight, "line-height":this._thumbHeight + "px"}).mousedown(preventDefault);
			if (this._selectMouseover) {
				this._$thumbs.bind("mouseover", {elem:this}, this.selectItem);
			}
			else {
				this._$thumbPanel.bind("click", {elem:this}, this.selectItem);
			}
			if (this._cpVertical) {
				this._$thumbs.css("margin-bottom", this._margin);
				this._$list.width(this._$thumbs.outerWidth());
				this._$thumbPanel.width(this._$list.width());
				if (MSIE7_BELOW) {
					this._$thumbPanel.height(this._numItems * this._$thumbs.outerHeight(true));
				}
				//check uneven size
				if (('small' == this._dbuttonsType || this._displayPlayBtn) && (this._buttonWidth > this._thumbWidth)) {
					var m = this._buttonWidth - this._thumbWidth;
					switch (ALIGN[this._cpAlign]) {
						case ALIGN["RT"]: case ALIGN["RC"]: case ALIGN["RB"]:
							this._$thumbPanel.css("margin-left", m);
							break;
						default:
							this._$thumbPanel.css("margin-right", m);
					}
				}
				
				//check overflow
				var maxHeight = this._screenHeight - (this._$buttonPanel.height() + this._margin);
				if (this._$thumbPanel.height() > maxHeight) {
					var unitSize = this._$thumbs.outerHeight(true);
					this._$list.addClass("inside").height(this._numItems * unitSize);
					this._$thumbPanel.css({height:Math.floor(maxHeight/unitSize) * unitSize - this._margin, "margin-bottom":this._margin});
					var range = this._$thumbPanel.height() - (this._$list.height() - this._margin);
					
					this._$thumbPanel.append("<div class='back-scroll'></div><div class='fwd-scroll'></div>");
					var $backScroll = this._$thumbPanel.find(".back-scroll");
					var $fwdScroll = this._$thumbPanel.find(".fwd-scroll");
					$backScroll.css({height:unitSize, width:"100%"});
					$fwdScroll.css({height:unitSize, width:"100%", top:"100%", "margin-top":-unitSize});
					
					if (!window.Touch) {
						$backScroll.bind("mouseenter", 
									function() {
										$fwdScroll.show();
										var speed = -that._$list.stop(true).position().top * SCROLL_RATE;
										that._$list.stop(true).animate({top:0}, speed, "linear", function() { $backScroll.hide(); });
									}).bind("mouseleave", {elem:this}, this.stopList);
						$fwdScroll.bind("mouseenter", 
									function() {
										$backScroll.show();
										var speed = (-range + that._$list.stop(true).position().top) * SCROLL_RATE;
										that._$list.stop(true).animate({top:range}, speed, "linear", function() { $fwdScroll.hide(); });
									}).bind("mouseleave", {elem:this}, this.stopList);
					}
					else {
						 $backScroll.hide();
						 $fwdScroll.hide();
					}
					
					this._$rotator.bind(UPDATE_LIST, function() {
						if(!that._$list.is(":animated")) {								
							var pos = that._$list.position().top + (that._currIndex * unitSize);
							if (pos < 0 || pos > that._$thumbPanel.height() - that._$thumbs.outerHeight()) {
								pos = -that._currIndex * unitSize;
								if (pos < range) {
									pos = range;
								}
								that._$list.stop(true).animate({top:pos}, ANIMATE_SPEED, 
																function() {
																	if (!window.Touch) {
																		$(this).position().top == 0 ? $backScroll.hide() : $backScroll.show();
																		$(this).position().top == range ? $fwdScroll.hide() : $fwdScroll.show();
																	}
																});
							}
						}
					});
				}
			}
			else {
				this._$thumbs.css("margin-right", this._margin);
				this._$list.height(this._$thumbs.outerHeight());
				this._$thumbPanel.height(this._$list.height());
				if (MSIE7_BELOW) {
					this._$thumbPanel.width(this._numItems * this._$thumbs.outerWidth(true));
				}
				//check uneven size
				if (('small' == this._dbuttonsType || this._displayPlayBtn) && this._buttonHeight > this._thumbHeight) {
					var m = this._buttonHeight - this._thumbHeight;
					switch (ALIGN[this._cpAlign]) {
						case ALIGN["TL"]: case ALIGN["TC"]: case ALIGN["TR"]:
							this._$thumbPanel.css("margin-bottom", m);

							break;
						default:
							this._$thumbPanel.css("margin-top", m);
					}
				}
				
				//check overflow
				var maxWidth =  this._screenWidth - (this._$buttonPanel.width() + this._margin);
				if (this._$thumbPanel.width() > maxWidth) {							
					var unitSize = this._$thumbs.outerWidth(true);
					this._$list.addClass("inside").width(this._numItems * unitSize);
					this._$thumbPanel.css({width:Math.floor(maxWidth/unitSize) * unitSize - this._margin, "margin-right":this._margin});
					var range = this._$thumbPanel.width() - (this._$list.width() - this._margin);
					
					this._$thumbPanel.append("<div class='back-scroll'></div><div class='fwd-scroll'></div>");
					var $backScroll = this._$thumbPanel.find(".back-scroll");
					var $fwdScroll = this._$thumbPanel.find(".fwd-scroll");
					$backScroll.css({width:unitSize, height:"100%"});
					$fwdScroll.css({width:unitSize, height:"100%", left:"100%", "margin-left":-unitSize});
					
					if (!window.Touch) {
						$backScroll.bind("mouseenter", 	function() {
															$fwdScroll.show();
															var speed = -that._$list.stop(true).position().left * SCROLL_RATE;
															that._$list.stop(true).animate({left:0}, speed, "linear", function() { $backScroll.hide(); });  
														}).bind("mouseleave", {elem:this}, this.stopList);
						
						$fwdScroll.bind("mouseenter", 	function() {
															$backScroll.show();
															var speed = (-range + that._$list.stop(true).position().left) * SCROLL_RATE;
															that._$list.stop(true).animate({left:range}, speed, "linear", function() { $fwdScroll.hide(); });  		  
														}).bind("mouseleave", {elem:this}, this.stopList);
					}
					
					this._$rotator.bind(UPDATE_LIST, function() {
						if(!that._$list.is(":animated")) {								
							var pos = that._$list.position().left + (that._currIndex * unitSize);
							if (pos < 0 || pos > that._$thumbPanel.width() - that._$thumbs.outerWidth()) {
								pos = -that._currIndex * unitSize;
								if (pos < range) {
									pos = range;
								}
								that._$list.stop(true).animate({left:pos}, ANIMATE_SPEED, 
																function() { 
																	$(this).position().left == 0 ? $backScroll.hide() : $backScroll.show();
																	$(this).position().left == range ? $fwdScroll.hide() : $fwdScroll.show();
																});
							}
						}
					});
				}
			}
			
			this.initTooltip();
		}
	}			
	
	//init layer data
	Rotator.prototype.initLayerData = function($item, minZIndex) {				
		var that = this;
		var $divs = $item.find(">div:hidden").not(".tt-text");
		var $sortedDivs = $divs.sort(function(a, b) { return getNonNegNumber($(a).attr('data-delay'), 0) - getNonNegNumber($(b).attr('data-delay'), 0); });
		$divs.remove();
		$item.append($sortedDivs);
		
		var $layer = this._$layers.eq(0);
		var $innerText = $layer.find(">div.inner-text");
		$sortedDivs.each(function(n) {
			var effect, duration, easing, delay;
			var $div = $(this);
			//calculate width and height
			var width =  getPosNumber($div.width(), 'auto');
			var height = getPosNumber($div.height(), 'auto');
			var totalPadding = $div.outerWidth() - $div.width();
			var padding = Math.round(totalPadding/2);
			
			var useBottom = !isNaN(parseInt($div.css("bottom")));
			var useRight = !isNaN(parseInt($div.css("right")));
			var top = "", bottom = "", left = "", right = "";
			
			if (useBottom)
				bottom = getNonNegNumber($div.css("bottom"), 0);
			else		
				top = getNonNegNumber($div.css("top"), 0);
			
			if (useRight)
				right = getNonNegNumber($div.css("right"), 0);
			else
				left = getNonNegNumber($div.css("left"), 0);
				
			$layer.css({top:top, bottom:bottom, left:left, right:right});
			
			$innerText.css({padding:padding, width:width, height:height}).html($div.html());
			if ('auto' == height) {
				height = $innerText.height() + 1;
			}
			height += totalPadding;
			
			if ('auto' == width) {
				width = $innerText.width() + 1;
			}
			width += totalPadding;
			
			var zIndex = getNonNegNumber($div.css("z-index"), 0) + minZIndex;
			if (zIndex > that._zIndex) {
				that._zIndex = zIndex;
			}
			$div.css({width:width, height:height});
			
			effect = getDefinedVal($div.attr("data-effect"), that._textEffect);
			duration = getPosNumber($div.attr("data-duration"), that._textDuration);	
			easing = getDefinedVal($div.attr("data-easing"), that._textEasing);	
			delay = getNonNegNumber($div.attr("data-delay"), (n * that._textDelay));
		
			if (endsWith(easing, 'Elastic') || endsWith(easing, 'Bounce')) {
				that._cssTrsnLayer = false;
			}
			
			$div.data({top:top, bottom:bottom, left:left, right:right, padding:padding, zindex:zIndex, usebottom:useBottom, useright:useRight, 
					   effect:effect, duration:duration, easing:easing, delay:delay});
		});
	}
	
	//init tool tip
	Rotator.prototype.initTooltip = function() {
		if ("text" == this._tipType) {
			var uid = 'tip-' + $("body").find(".rotator-tooltip").length;
			$("body").append("<div class='rotator-tooltip' id='" + uid + "'><div class='tt-txt'></div></div>");
			this._$tooltip = $("body").find("#" + uid);
			this._$tooltip.find(">.tt-txt").css({width:this._tooltipWidth, height:this._tooltipHeight});
			this._$thumbs.bind("mouseover", {elem:this}, this.showTooltip).bind("mouseout", {elem:this}, this.hideTooltip).bind("mousemove", {elem:this}, this.moveTooltip);
			switch (ALIGN[this._cpAlign]) {
				case ALIGN["TL"]: case ALIGN["TC"]: case ALIGN["TR"]:
					this._$tooltip.data("bottom",true).addClass("txt-down");
					break;
				default:
					this._$tooltip.data("bottom",false).addClass("txt-up");
			}
		}
		else if ("image" == this._tipType) {
			var that = this;
			var uid = 'tip-' + $("body").find(".rotator-tooltip").length;
			$("body").append("<div class='rotator-tooltip' id='" + uid + "'><div class='img-frame'></div></div>");
			this._$tooltip = $("body").find("#" + uid);
			var $frame = this._$tooltip.find(">div.img-frame");
			$frame.css({width:this._tooltipWidth, height:this._tooltipHeight});
			
			this._$thumbs.each(function(n) {
				var $img = $(this).find(">img.tt-img");
				if (0 < $img.length) {
					$img.attr("id", "tt-img-" + n);
					$frame.append($img);
					
					$img.one("load", function() {
						that.maximizeImage($(this), that._tooltipWidth, that._tooltipHeight);						
					});
					
					if ($img[0].complete || "complete" == $img[0].readyState)
						$img.trigger("load");
				}
			});
			
			switch (ALIGN[this._cpAlign]) {
				case ALIGN["TL"]: case ALIGN["TC"]: case ALIGN["TR"]:
					this._$thumbs.bind("mouseover", {elem:this}, this.showHImgTooltip);
					this._$tooltip.data("bottom",true).addClass("img-down");
					break;
				case ALIGN["LT"]: case ALIGN["LC"]: case ALIGN["LB"]:
					this._$thumbs.bind("mouseover", {elem:this}, this.showVImgTooltip);
					this._$tooltip.data("right",true).addClass("img-right");
					break;
				case ALIGN["RT"]: case ALIGN["RC"]: case ALIGN["RB"]:
					this._$thumbs.bind("mouseover", {elem:this}, this.showVImgTooltip);
					this._$tooltip.data("right",false).addClass("img-left");
					break;
				default:
					this._$thumbs.bind("mouseover", {elem:this}, this.showHImgTooltip);
					this._$tooltip.data("bottom",false).addClass("img-up");
			}
			this._$thumbs.bind("mouseout", {elem:this}, this.hideTooltip);	
		}
		
		if (msieCheck(6)) {
			try {
				this._$tooltip.css("background-image", "none").children().css("margin",0);
			}
			catch (ex) {
			}
		}
	}
	
	//show image tooltip
	Rotator.prototype.showHImgTooltip = function(e) {
		var that = e.data.elem;
		var $img = that._$tooltip.find("img#tt-img-" + $(this).index());
		if ($img.attr("src")) {
			that._$tooltip.find("img").css({zIndex:0}).hide();
			$img.css({zIndex:1}).show();	
			var yOffset = that._$tooltip.data("bottom") ? $(this).outerHeight() : -that._$tooltip.outerHeight();
			var offset = $(this).offset();
			that._$tooltip.css({top:offset.top + yOffset, left:offset.left + (($(this).outerWidth() - that._$tooltip.outerWidth())/2)})
					.stop(true, true).delay(that._tooltipDelay).fadeIn(300);	
		}

	}
	
	//show image tooltip
	Rotator.prototype.showVImgTooltip = function(e) {
		var that = e.data.elem;
		var $img = that._$tooltip.find("img#tt-img-" + $(this).index());
		if ($img.attr("src")) {
			that._$tooltip.find("img").css({zIndex:0}).hide();
			$img.css({zIndex:1}).show();	
			var xOffset = that._$tooltip.data("right") ? $(this).outerWidth() : -that._$tooltip.outerWidth();
			var offset = $(this).offset();
			that._$tooltip.css({top:offset.top + (($(this).outerHeight() - that._$tooltip.outerHeight())/2), left:offset.left + xOffset})
					.stop(true, true).delay(that._tooltipDelay).fadeIn(300);
		}
	}
	
	//show tooltip
	Rotator.prototype.showTooltip = function(e) {
		var that = e.data.elem;
		var caption = that._$items[$(this).index()].data("ttText");
		if ("undefined" != typeof caption && "" != caption) {					
			that._$tooltip.find(">div.tt-txt").html(caption);
			var yOffset = that._$tooltip.data("bottom") ? 0 : -that._$tooltip.outerHeight(true);
			that._$tooltip.css({top:e.pageY + yOffset, left:e.pageX}).stop(true, true).delay(that._tooltipDelay).fadeIn(300);
		}
	}
	
	//tooltip move
	Rotator.prototype.moveTooltip = function(e) {
		var that = e.data.elem;
		var yOffset = that._$tooltip.data("bottom") ? 0 : -that._$tooltip.outerHeight(true);
		that._$tooltip.css({top:e.pageY + yOffset, left:e.pageX});
	}
	
	//hide tooltip
	Rotator.prototype.hideTooltip = function(e) {
		try {
			var that = (typeof e != "undefined") ? e.data.elem : this;
			that._$tooltip.stop(true, true).hide();
		}
		catch(ex) {
		}	
	}
	
	//display control panel
	Rotator.prototype.displayCPanel = function(e) {
		var that = e.data.elem;
		var prop = {};
		prop[e.data.dir] = that._$cpanel.data("pos");
		prop["opacity"] = 1;
		that._$cpanel.stop(true).animate(prop, ANIMATE_SPEED);
	}
	
	//hide control panel
	Rotator.prototype.hideCPanel = function(e) {
		var that = e.data.elem;
		var prop = {};
		prop[e.data.dir] = that._$cpanel.data("offset");
		prop["opacity"] = 0;
		that._$cpanel.stop(true).animate(prop, ANIMATE_SPEED);
	}
	
	Rotator.prototype.showSideButtons = function(e) {
		var that = e.data.elem;
		that._$sPrev.stop(true).animate({left:0}, ANIMATE_SPEED);
		that._$sNext.stop(true).animate({"margin-left":-that._$sNext.width()}, ANIMATE_SPEED);
	}
	
	Rotator.prototype.hideSideButtons = function(e) {
		var that = e.data.elem;
		that._$sPrev.stop(true).animate({left:-that._$sPrev.width()}, ANIMATE_SPEED);
		that._$sNext.stop(true).animate({"margin-left":0}, ANIMATE_SPEED);
	}
	
	//select list item
	Rotator.prototype.selectItem = function(e) {
		var that = e.data.elem;
		var $item = $(e.target);
		if ($item[0].nodeName != "LI") {
			$item = $item.closest("li");
		}
		var i = $item.index();
		if (i > -1 && i != that._currIndex) {	
			that._dir = i < that._currIndex ? PREV : NEXT; 
			that.resetTimer();
			that._prevIndex = that._currIndex;
			that._currIndex = i;
			that.loadContent(that._currIndex);
			that.hideTooltip();
		}
		return false;
	}
	
	//go to previous image
	Rotator.prototype.prevImg = function(e) {
		var that = (typeof e != "undefined") ? e.data.elem : this;
		that._dir = PREV;
		that.resetTimer();
		that._prevIndex = that._currIndex;
		that._currIndex = (that._currIndex > 0) ? (that._currIndex - 1) : (that._numItems - 1);
		that.loadContent(that._currIndex);
		return false;
	}
	
	//go to next image
	Rotator.prototype.nextImg = function(e) {
		var that = (typeof e != "undefined") ? e.data.elem : this;
		that._dir = NEXT;
		that.resetTimer();
		that._prevIndex = that._currIndex;
		that._currIndex = (that._currIndex < that._numItems - 1) ? (that._currIndex + 1) : 0;
		that.loadContent(that._currIndex);
		return false;
	}
	
	//play/pause
	Rotator.prototype.togglePlay = function(e) {
		var that = e.data.elem;
		that._rotate = !that._rotate;
		that._$playBtn.toggleClass("pause", that._rotate);
		that._rotate ? that.startTimer() : that.pauseTimer();
		return false;
	}
	
	//play
	Rotator.prototype.play = function(e) {
		var that = e.data.elem;
		that._rotate = true;
		that._$playBtn.addClass("pause");
		that.startTimer();
	}

	//pause
	Rotator.prototype.pause = function(e) {
		var that = e.data.elem;
		that._rotate = false;
		that._$playBtn.removeClass("pause");
		that.pauseTimer();
	}
	
	//pause on last item
	Rotator.prototype.pauseLast = function(i) {
		if (i == this._numItems - 1) {
			this._rotate = false;
			this._$playBtn.removeClass("pause");
		}
	}
	
	//update layers
	Rotator.prototype.updateLayers = function(e) {
		var that = e.data.elem;
		that._$layers.stop(true, true);
		if (null === that._layerId) {
			var i = 0;
			var $divs = that._$items[that._currIndex].find(">div:hidden").not(".tt-text");
			if (i < $divs.length) {
				that._layerDelay = $divs.eq(i).data("delay");
				that._layerId = setTimeout(function() { that.updateLayer(i, $divs); }, that._layerDelay);
			}
		}
	}
	
	Rotator.prototype.updateLayer = function(i, $divs) {
		var $layer = this._$layers.eq(i);
		var $div = $divs.eq(i);
		
		var layerWidth = $div.width();
		var layerHeight = $div.height();
		var useBottom = $div.data("usebottom");
		var useRight = $div.data("useright");
		var layerTop, layerBottom, layerLeft, layerRight;
		layerTop = $div.data("top");
		layerBottom = $div.data("bottom");
		layerLeft = $div.data("left");
		layerRight = $div.data("right");
		
		//update layer
		$layer.css("z-index", $div.data("zindex"));
		$layer.find(">div.inner-text").css({color:$div.css("color"), padding:$div.data("padding")});
		$layer.find(">div.inner-bg").css({height:layerHeight, backgroundColor:$div.css("background-color"), opacity:$div.css("opacity"), 
										  backgroundImage:$div.css("background-image"), backgroundRepeat:$div.css("background-repeat"), backgroundPosition:$div.css("background-position")});
		//display layer
		switch(TEXT_EFFECTS[$div.data('effect')]) {
			case TEXT_EFFECTS["fade"]:
				this.fadeInLayer($div, $layer, {top:layerTop, bottom:layerBottom, left:layerLeft, right:layerRight, width:layerWidth, height:layerHeight});
				break;
				
			case TEXT_EFFECTS["expandDown"]:
				if (useBottom) {
					layerTop = (this._screenHeight - layerHeight) - layerBottom;
				}
				this.expandLayer($div, $layer, {width:layerWidth, height:0, top:layerTop, left:layerLeft, right:layerRight}, {height:layerHeight});
				break;	
			
			case TEXT_EFFECTS["expandUp"]:
				if (!useBottom) {
					layerBottom = this._screenHeight - (layerTop + layerHeight);
				}
				this.expandLayer($div, $layer, {width:layerWidth, height:0, bottom:layerBottom, left:layerLeft, right:layerRight}, {height:layerHeight});
				break;
			
			case TEXT_EFFECTS["expandRight"]:
				if (useRight) {
					layerLeft = (this._screenWidth - layerWidth) - layerRight;
				}
				this.expandLayer($div, $layer, {width:0, height:layerHeight, top:layerTop, bottom:layerBottom, left:layerLeft}, {width:layerWidth});
				break;	
			
			case TEXT_EFFECTS["expandLeft"]:
				if (!useRight) {
					layerRight = this._screenWidth - (layerLeft + layerWidth);
				}
				this.expandLayer($div, $layer, {width:0, height:layerHeight, top:layerTop, bottom:layerBottom, right:layerRight}, {width:layerWidth});
				break;
			
			case TEXT_EFFECTS["moveDown"]:
				if (useBottom)
					this.moveLayer($div, $layer, {width:layerWidth, height:layerHeight, bottom:this._screenHeight, left:layerLeft, right:layerRight}, {bottom:layerBottom});
				else
					this.moveLayer($div, $layer, {width:layerWidth, height:layerHeight, top:-layerHeight, left:layerLeft, right:layerRight}, {top:layerTop});
				break;
			
			case TEXT_EFFECTS["moveUp"]:
				if (useBottom)
					this.moveLayer($div, $layer, {width:layerWidth, height:layerHeight, bottom:-layerHeight, left:layerLeft, right:layerRight}, {bottom:layerBottom});
				else
					this.moveLayer($div, $layer, {width:layerWidth, height:layerHeight, top:this._screenHeight, left:layerLeft, right:layerRight}, {top:layerTop});
				break;
			
			case TEXT_EFFECTS["moveRight"]:
				if (useRight)
					this.moveLayer($div, $layer, {width:layerWidth, height:layerHeight, top:layerTop, bottom:layerBottom, right:this._screenWidth}, {right:layerRight});
				else
					this.moveLayer($div, $layer, {width:layerWidth, height:layerHeight, top:layerTop, bottom:layerBottom, left:-layerWidth}, {left:layerLeft});
				break;
			
			case TEXT_EFFECTS["moveLeft"]:
				if (useRight)
					this.moveLayer($div, $layer, {width:layerWidth, height:layerHeight, top:layerTop, bottom:layerBottom, right:-layerWidth}, {right:layerRight});
				else
					this.moveLayer($div, $layer, {width:layerWidth, height:layerHeight, top:layerTop, bottom:layerBottom, left:this._screenWidth}, {left:layerLeft});
				break;
			
			default:
				this.showLayer($div, $layer, {top:layerTop, bottom:layerBottom, left:layerLeft, right:layerRight, width:layerWidth, height:layerHeight});
		}
		
		if (++i < $divs.length) {
			var that = this;
			var $div = $divs.eq(i);
			var delay = $div.data("delay");
			var layerDelay = Math.abs(delay - this._layerDelay);
			this._layerDelay = delay;
			this._layerId = setTimeout(function() { that.updateLayer(i, $divs); }, layerDelay);
		}
	}
	
	//update layers
	Rotator.prototype.updateCssLayers = function(e) {
		var that = e.data.elem;
		that._$layers.cssTransitionStop(true);	
		var $divs = that._$items[that._currIndex].find(">div:hidden").not(".tt-text");
		$divs.each(function(n) { 
			that.updateCssLayer($(this), that._$layers.eq(n)); 
		});
	}
	
	Rotator.prototype.updateCssLayer = function($div, $layer) {
		var layerWidth, layerHeight, layerTop, layerBottom, layerLeft, layerRight;
		layerWidth = $div.width();
		layerHeight = $div.height();
		layerTop = $div.data("top");
		layerBottom = $div.data("bottom");
		layerLeft = $div.data("left");
		layerRight = $div.data("right");
		
		//update layer
		$layer.css("z-index", $div.data("zindex"));
		$layer.find(">div.inner-text").css({color:$div.css("color"), padding:$div.data("padding")});
		$layer.find(">div.inner-bg").css({height:layerHeight, backgroundColor:$div.css("background-color"), opacity:$div.css("opacity"), 
										  backgroundImage:$div.css("background-image"), backgroundRepeat:$div.css("background-repeat"), backgroundPosition:$div.css("background-position")});
		//display layer
		switch(TEXT_EFFECTS[$div.data('effect')]) {
			
			case TEXT_EFFECTS["fade"]:
				this.fadeInCssLayer($div, $layer, {top:layerTop, bottom:layerBottom, left:layerLeft, right:layerRight, width:layerWidth, height:layerHeight, opacity:0});
				break;
				
			case TEXT_EFFECTS["expandDown"]:
				if ($div.data("usebottom")) {
					layerTop = (this._screenHeight - layerHeight) - layerBottom;
				}
				this.expandCssLayer($div, $layer, {width:layerWidth, height:0, top:layerTop, left:layerLeft, right:layerRight}, {height:layerHeight});
				break;	
			
			case TEXT_EFFECTS["expandUp"]:
				if (!$div.data("usebottom")) {
					layerBottom = this._screenHeight - (layerTop + layerHeight);
				}
				this.expandCssLayer($div, $layer, {width:layerWidth, height:0, bottom:layerBottom, left:layerLeft, right:layerRight}, {height:layerHeight});
				break;
			
			case TEXT_EFFECTS["expandRight"]:
				if ($div.data("useright")) {
					layerLeft = (this._screenWidth - layerWidth) - layerRight;
				}
				this.expandCssLayer($div, $layer, {width:0, height:layerHeight, top:layerTop, bottom:layerBottom, left:layerLeft}, {width:layerWidth});
				break;	
			
			case TEXT_EFFECTS["expandLeft"]:
				if (!$div.data("useright")) {
					layerRight = this._screenWidth - (layerLeft + layerWidth);
				}
				this.expandCssLayer($div, $layer, {width:0, height:layerHeight, top:layerTop, bottom:layerBottom, right:layerRight}, {width:layerWidth});
				break;
			
			case TEXT_EFFECTS["moveDown"]:
				if ($div.data("usebottom"))
					this.moveCssLayer($div, $layer, {width:layerWidth, height:layerHeight, bottom:this._screenHeight, left:layerLeft, right:layerRight}, {bottom:layerBottom});
				else
					this.moveCssLayer($div, $layer, {width:layerWidth, height:layerHeight, top:-layerHeight, left:layerLeft, right:layerRight}, {top:layerTop});
				break;
			
			case TEXT_EFFECTS["moveUp"]:
				if ($div.data("usebottom"))
					this.moveCssLayer($div, $layer, {width:layerWidth, height:layerHeight, bottom:-layerHeight, left:layerLeft, right:layerRight}, {bottom:layerBottom});
				else
					this.moveCssLayer($div, $layer, {width:layerWidth, height:layerHeight, top:this._screenHeight, left:layerLeft, right:layerRight}, {top:layerTop});
				break;
			
			case TEXT_EFFECTS["moveRight"]:
				if ($div.data("useright"))
					this.moveCssLayer($div, $layer, {width:layerWidth, height:layerHeight, top:layerTop, bottom:layerBottom, right:this._screenWidth}, {right:layerRight});
				else
					this.moveCssLayer($div, $layer, {width:layerWidth, height:layerHeight, top:layerTop, bottom:layerBottom, left:-layerWidth}, {left:layerLeft});
				break;
			
			case TEXT_EFFECTS["moveLeft"]:
				if ($div.data("useright"))
					this.moveCssLayer($div, $layer, {width:layerWidth, height:layerHeight, top:layerTop, bottom:layerBottom, right:-layerWidth}, {right:layerRight});
				else
					this.moveCssLayer($div, $layer, {width:layerWidth, height:layerHeight, top:layerTop, bottom:layerBottom, left:this._screenWidth}, {left:layerLeft});
				break;
			
			default:
				this.showCssLayer($div, $layer, {top:layerTop, bottom:layerBottom, left:layerLeft, right:layerRight, width:layerWidth, height:layerHeight, opacity:1});
		}
	}
	
	//reset layers
	Rotator.prototype.resetLayers = function(e) {
		var that = e.data.elem;
		clearTimeout(that._syncId);
		clearTimeout(that._layerId);
		that._layerId = null;
		that._syncId = null;
		that._$layers.stop(true, true);
		that._$layers.each(function(n) {
			var $layer = $(this);
			if ($layer.is(":visible")) {
			//	if (IS_MSIE) {
				//	$layer.find(">div.inner-text").css("opacity", 0);
			//	}
				$layer.fadeOut(ANIMATE_SPEED);
			}
		});
	}
	
	//reset layers by css
	Rotator.prototype.resetCssLayers = function(e) {
		var that = e.data.elem;
		clearTimeout(that._syncId);
		that._syncId = null;
		that._$layers.cssTransitionStop(true);
		that._$layers.each(function(n) {
			var $layer = $(this);
			if ($layer.is(":visible")) {
				$layer.cssTransition({opacity:0}, ANIMATE_SPEED, '', 0, function() { $(this).css({display:'none'}); });
			}
		});
	}
	
	//expand layer
	Rotator.prototype.expandLayer = function($div, $layer, props1, props2) {
		$layer.find(">div.inner-text").html("");
		$layer.stop(true, true).css({top:"", bottom:"", left:"", right:""}).css(props1).show()
			  .animate(props2, $div.data("duration"), $div.data("easing"),
			function () {
				$(this).find(">div.inner-text").html($div.html());
			});  		
	}
	
	//move layer
	Rotator.prototype.moveLayer = function($div, $layer, props1, props2) {
		$layer.find(">div.inner-text").html($div.html());
		$layer.stop(true, true).css({top:"", bottom:"", left:"", right:""}).css(props1).show()
			  .animate(props2, $div.data("duration"), $div.data("easing"));
	}
	
	//fade in layer
	Rotator.prototype.fadeInLayer = function($div, $layer, props) {
		$layer.find(">div.inner-text").html($div.html());
		$layer.stop(true, true).css(props).fadeIn($div.data("duration"), $div.data("easing"), function() {
															if (IS_MSIE) {
																$(this).find(">div.inner-text").get(0).style.removeAttribute('filter'); 
															}}); 
		
	}
	
	//show layer
	Rotator.prototype.showLayer = function($div, $layer, props) {
		$layer.find(">div.inner-text").html($div.html());
		$layer.stop(true,true).css(props).show();
	}
	
	//expand layer
	Rotator.prototype.expandCssLayer = function($div, $layer, props1, props2) {
		$layer.find(">div.inner-text").html("");
		$layer.css({top:"", bottom:"", left:"", right:"", opacity:1}).css(props1).show();
		$layer.cssTransition(props2, $div.data("duration"), $div.data("easing"), $div.data("delay"), function(){
			$(this).find(">div.inner-text").html($div.html());
		});  		
	}
	
	//move layer
	Rotator.prototype.moveCssLayer = function($div, $layer, props1, props2) {
		$layer.find(">div.inner-text").html($div.html());
		$layer.css({top:"", bottom:"", left:"", right:"", opacity:1}).css(props1).show();
		$layer.cssTransition(props2, $div.data("duration"), $div.data("easing"), $div.data("delay"));
	}
	
	//fade in layer
	Rotator.prototype.fadeInCssLayer = function($div, $layer, props) {
		$layer.find(">div.inner-text").html($div.html());
		$layer.css(props).show(); 
		$layer.cssTransition({opacity:1}, $div.data("duration"), $div.data("easing"), $div.data("delay"));	
	}
	
	//show layer
	Rotator.prototype.showCssLayer = function($div, $layer, props) {
		$layer.find(">div.inner-text").html($div.html());
		$layer.css(props).show();
	}
	
	//display layers on mouseover
	Rotator.prototype.displayLayers = function(e) {
		var that = e.data.elem;
		that._$rotator.unbind(UPDATE_LAYERS).bind(UPDATE_LAYERS, {elem:that}, that.updateLayers).trigger(UPDATE_LAYERS);
	}

	//hide layers on mouseout
	Rotator.prototype.hideLayers = function(e) {
		var that = e.data.elem;
		that._$rotator.unbind(UPDATE_LAYERS).trigger(RESET_LAYERS);
	}
	
	//display layers on mouseover
	Rotator.prototype.displayCssLayers = function(e) {
		var that = e.data.elem;
		that._$rotator.unbind(UPDATE_LAYERS).bind(UPDATE_LAYERS, {elem:that}, that.updateCssLayers).trigger(UPDATE_LAYERS);
	}
	
	//load current content
	Rotator.prototype.loadContent = function(i) {
		var $item = this._$items[i];
		
		this._$rotator.trigger(RESET_LAYERS).trigger(UPDATE_LIST);
		if (this._playOnce) {
			this.pauseLast(i);
		}
		
		//select thumb
		this._$thumbs.filter(".curr-thumb").removeClass("curr-thumb");
		this._$thumbs.eq(i).addClass("curr-thumb");
		
		//set delay
		this._delay = $item.data("delay");
		
		if (!this._textSync) {
			this._$rotator.trigger(UPDATE_LAYERS);
		}
		
		//set link
		if (this._$mainLink) {
			var href = $item.data("href");	
			if (href) {
				var target = $item.data("target");
				this._$mainLink.unbind("click", preventDefault).css("cursor", "pointer").attr({href:href, target:target});
			}
			else {
				this._$mainLink.click(preventDefault).css("cursor", "default");
			}
		}
		
		//load image
		if ($item.data("complete")) {
			this._$preloader.hide();
			this.displayContent($item.data("img"));
		}	
		else {	
			//load new image
			var that = this;
			var $img = $item.data('img');
			$img.one("load",
				function() {
					that._$preloader.hide();
					if (!$item.data("complete")) {
						that.storeImg($item, $(this));
					}
					that.displayContent($(this));
				}
			).error(
				function() {
				//	alert("Error loading image");
				}
			);
			this._$preloader.show();
			$img.attr("src", $item.data("imgurl"));
			
			if ($img[0].complete || $img[0].readyState == "complete") {
				$img.trigger("load");
			}
		}	    
	}
	
	//display content
	Rotator.prototype.displayContent = function($img) {
		//clear
		if (this._vStripeEffect) {
			this._vStripes.clear();
		}
		if (this._hStripeEffect) {
			this._hStripes.clear();
		}
		if (this._blockEffect) {
			this._blocks.clear();
		}
		if (this._vStripeEffect || this._hStripeEffect || this._blockEffect) {
			this.setPrevious();
		}

		var $item = this._$items[this._currIndex];
		var effect = $item.data("effect");
		var duration = $item.data("duration");
		var easing = $item.data("easing");
		
		if (effect == EFFECTS["none"] || (typeof effect == "undefined")) {
			this.showContent($img);
			return;
		}
		else if (effect == EFFECTS["fade"]) {
			this.fadeInContent($img, duration, easing);
			return;
		}
		else if (effect == EFFECTS["crossFade"]) {
			this.xfadeContent($img, duration, easing);
			return;
		}
		else if (effect == EFFECTS["horizontalSlide"]) {
			this.slideContent($img, "left", this._screenWidth, duration, easing);
			return;
		}
		else if (effect == EFFECTS["verticalSlide"]) {
			this.slideContent($img, "top", this._screenHeight, duration, easing);
			return;
		}
		
		if (effect == EFFECTS["random"]) {
			effect = Math.floor(Math.random() * (NUM_EFFECTS - 6));
		}
		
		if (effect <= EFFECTS["spiralOut"]) {
			this._blocks.displayContent($img, effect, duration, easing);
		}
		else if (effect <= EFFECTS["verticalSliceRandomFade"]) {
			this._vStripes.displayContent($img, effect, duration, easing);
		}
		else {
			this._hStripes.displayContent($img, effect, duration, easing);
		}
	}
	
	//set previous
	Rotator.prototype.setPrevious = function() {
		if (this._prevIndex >= 0) {
			var currSrc = this._$mainLink.find("img#curr-img").data("src");
			var prevSrc = this._$items[this._prevIndex].data("imgurl");
			if (currSrc != prevSrc) {
				this._$mainLink.find("img.main-img").attr("id","").hide();
				var $img = this._$mainLink.find("img.main-img").filter(function() { return $(this).data("src") == prevSrc; });
				$img.eq(0).show();
			}
		}
	}
	
	//display content (no effect)
	Rotator.prototype.showContent = function($img) {
		if (this._textSync) {
			this._$rotator.trigger(UPDATE_LAYERS);
		}
		this._$mainLink.find("img.main-img").attr("id","").hide();
		$img.attr("id", "curr-img").show();
		this.startTimer();
	}
	
	//display content (fade effect)
	Rotator.prototype.fadeInContent = function($img, duration, easing) {
		var that = this;
		this._$mainLink.find("img#curr-img").stop(true, true);
		this._$mainLink.find("img.main-img").attr("id","").css("z-index", 0);
		$img.attr("id", "curr-img").stop(true, true).css({opacity:0,"z-index":1}).show().animate({opacity:1}, duration, easing,
			function() {
				that._$mainLink.find("img.main-img:not('#curr-img')").hide();
				that.startTimer();
			}
		);
		
		if (this._textSync) {
			this._syncId = setTimeout(function() { that._$rotator.trigger(UPDATE_LAYERS); }, duration);
		}
	}
	
	//display content (cross fade effect)
	Rotator.prototype.xfadeContent = function($img, duration, easing) {
		var that = this;
		var $prevImg = this._$mainLink.find("img#curr-img");
		this._$mainLink.find("img.main-img").attr("id","").css("z-index", 0);
		$prevImg.stop(true, true).animate({opacity:0}, duration, easing);
		$img.attr("id", "curr-img").stop(true, true).css({opacity:0,"z-index":1}).show().animate({opacity:1}, duration, easing,
			function() {
				that._$mainLink.find("img.main-img:not('#curr-img')").hide();
				that.startTimer();
			}
		);
		
		if (this._textSync) {
			this._syncId = setTimeout(function() { that._$rotator.trigger(UPDATE_LAYERS); }, duration);
		}
	}
	
	//slide content
	Rotator.prototype.slideContent = function($currImg, pos, moveby, duration, easing) {
		this._$strip.stop(true,true);
		var $prevImg = $("#curr-img", this._$strip);
		if ($prevImg.length > 0) {
			this._$strip.find(".main-img").attr("id","").closest(".content-box").css({top:0,left:0});
			$currImg.attr("id", "curr-img").closest(".content-box").css('visibility', 'visible');
			var $img, dest;
			if (this._dir == PREV) {
				this._$strip.css(pos, -moveby);
				$img = $prevImg;
				dest = 0;
			}
			else {
				$img = $currImg;
				dest = -moveby;
			}
			$img.closest(".content-box").css(pos,moveby);
			var prop = (pos == "top") ? {top:dest} : {left:dest};
			var that = this;
			this._$strip.stop(true,true).animate(prop, duration, easing,
								function() {
									that._$strip.find(".main-img:not('#curr-img')").closest(".content-box").css('visibility', 'hidden');
									that._$strip.find("#curr-img").closest(".content-box").css('visibility', 'visible');
									$img.closest(".content-box").css({top:0,left:0});
									that._$strip.css({top:0,left:0});
									that.startTimer();
								});
			
			if (this._textSync) {
				this._syncId = setTimeout(function() { that._$rotator.trigger(UPDATE_LAYERS); }, duration);
			}
		}
		else {
			this._$strip.css({top:0,left:0});
			this._$strip.find(".main-img").closest(".content-box").css({visibility:'hidden', top:0,left:0});
			$currImg.attr("id", "curr-img").closest(".content-box").css('visibility', 'visible');
			if (this._textSync) {
				this._$rotator.trigger(UPDATE_LAYERS);
			}
			this.startTimer();
		}
	}
	
	//load image
	Rotator.prototype.loadImg = function(loadIndex) {
		try {
			var $item = this._$items[loadIndex];
			var $img = $item.data("img");
			var that = this;
			$img.one("load", function() {		  
				if (!$item.data("complete")) {
					that.storeImg($item, $(this));
				}
				loadIndex++
				if (loadIndex < that._numItems) {
					that.loadImg(loadIndex);
				}
			})
			.error(function() {
				//error loading image, continue next
				loadIndex++
				if (loadIndex < that._numItems) {
					that.loadImg(loadIndex);
				}
			});

			$img.attr("src", $item.data("imgurl"));
			
			if ($img[0].complete || $img[0].readyState == "complete") {
				$img.trigger("load");
			}
		}
		catch(ex) {}
	}
	
	Rotator.prototype.loadAll = function() {
		var that = this;
		for (var i = 0; i < this._$items.length; i++) {
			var $item = this._$items[i];
			var $img = $item.data("img");
			
			$img.one("load", {elem:$item}, function(e) {
				var $i = e.data.elem;									
				if (!$i.data("complete")) {
					that.storeImg($i, $(this));
				}
			});

			$img.attr("src", $item.data("imgurl"));
			
			if ($img[0].complete || $img[0].readyState == "complete") {
				$img.trigger("load");
			}
		}
	}
	
	//process & store image
	Rotator.prototype.storeImg = function($item, $img) {
		if (this._slideTransition) {
			var $link = $item.find(">a").eq(1);
			if (0 < $link.length) {
				$img.wrap($link);
			}
		}
		
		if (this._autoCenter)
			this.centerImg($img);
		
		var src = $img.attr('src');
		if (typeof(src) != "undefined") {
			var i = src.indexOf('?');
			if (i >= 0)
				src = src.substring(0, i);
				
			$img.data("src", src);
		}
		$item.data("complete",true);
	}
	
	//center image
	Rotator.prototype.centerImg = function($img) {
		var width = $img.width();
		var height = $img.height();
		if (width > 0 && height > 0) {
			$img.css({top:(this._screenHeight - height)/2, left:(this._screenWidth  - width)/2});
		}
	}
	
	//start timer
	Rotator.prototype.startTimer = function() {
		if (this._rotate && this._timerId === null) {
			var that = this;
			var duration = Math.round(this._$timer.data("pct") * this._delay);
			this._$timer.stop(true).animate({width:(this._screenWidth+1)}, duration, "linear");
			this._timerId = setTimeout(	function(e) {
											that._dir = NEXT;
											that.resetTimer();
											that._prevIndex = that._currIndex;
											that._currIndex = (that._currIndex < that._numItems - 1) ? (that._currIndex + 1) : 0;
											that.loadContent(that._currIndex);
										}, duration);
		}
	}
	
	//reset timer
	Rotator.prototype.resetTimer = function() {
		clearTimeout(this._timerId);
		this._timerId = null;
		this._$timer.stop(true).width(0).data("pct", 1);
	}
	
	//pause timer
	Rotator.prototype.pauseTimer = function() {
		clearTimeout(this._timerId);
		this._timerId = null;
		this._$timer.stop(true)
		var pct = 1 - (this._$timer.width()/(this._screenWidth+1));
		this._$timer.data("pct", pct);
	}
	
	Rotator.prototype.stopList = function(e) {
		e.data.elem._$list.stop(true);
	}
	
	//shuffle items
	Rotator.prototype.shuffleItems = function() {
		var items = this._$thumbs.toArray();
		for (var i = 0; i < this._numItems; i++) {
			var ri = Math.floor(Math.random() * this._numItems);
			var temp = items[i];
			items[i] = items[ri];
			items[ri] = temp;
		}
		
		for (var i = 0; i < this._numItems; i++) {
			this._$list.append($(items[i]));
		}
		
		this._$thumbs = this._$list.find(">li");
	}
	
	//check effect
	Rotator.prototype.checkEffect = function(num) {
		if (num == EFFECTS["random"]) {
			this._blockEffect = this._hStripeEffect = this._vStripeEffect = true;
		}
		else if (num <= EFFECTS["spiralOut"]) {
			this._blockEffect = true;
		}
		else if (num <= EFFECTS["verticalSliceRandomFade"]) {
			this._vStripeEffect = true;
		}
		else if (num <= EFFECTS["horizontalSliceRandomFade"]) {
			this._hStripeEffect = true;
		}
	}
	
	//maximize image
	Rotator.prototype.maximizeImage = function($img, boxWidth, boxHeight) {
		if ('auto' === boxWidth && 'auto' === boxHeight)
			return;
		
		var scale, width = $img.width(), height = $img.height();
		if (0 == width || 0 == height) 
			return;
		
		if ('auto' === boxHeight) {
			scale = boxWidth/width;
			width = boxWidth;	
			height *= scale;
			boxHeight = height; 
		}
		else if ('auto' === boxWidth) {
			scale = boxHeight/height;
			height = boxHeight;
			width *= scale;
			boxWidth = width;
		}
		else {
			var scaleW = boxWidth/width;
			var scaleH = boxHeight/height;
			scale = (scaleH > scaleW) ? scaleH : scaleW;
			width *= scale;
			height *= scale;	
		}
		
		$img.css({width:width, height:height, left:Math.round((boxWidth - width)/2), top:Math.round((boxHeight - height)/2)});
	}
	
	Rotator.prototype.getMaxLayers = function() {
		var arr = this._$thumbs.map(function() { return $(this).find(">div:hidden").not(".tt-text").length; }).get();
		arr.sort(function(a, b){ return b - a; });
		return arr[0];	
	}
	
	//mousewheel scroll content
	Rotator.prototype.mouseScrollContent = function(e) {
		var that = e.data.elem;
		if (!that._$strip.is(":animated")) {
			var delta = (typeof e.originalEvent.wheelDelta == "undefined") ?  -e.originalEvent.detail : e.originalEvent.wheelDelta;
			delta > 0 ? that.prevImg() : that.nextImg();
		}
		return false;
	}
	
	//prevent default behavior
	function preventDefault() {
		return false;
	}
	
	//get positive number
	function getPosNumber(val, defaultVal) {
		val = parseInt(val);
		if (!isNaN(val) && val > 0) {
			return val;
		}
		return defaultVal;
	}

	//get nonnegative number
	function getNonNegNumber(val, defaultVal) {
		val = parseInt(val);
		if (!isNaN(val) && val >= 0) {
			return val;
		}
		return defaultVal;
	}
	
	function getBoolean(val) {
		if (typeof val == "string") {
			val = val.toLowerCase();
			if (val == "true")
				return true;
			else
				return false;
		}
		
		return false;
	}
	
	function getEnum(val, enums, defaultVal) {
		for (var i = 0; i < enums.length; i++) {
			if (enums[i] == val)
				return val;
		}
		
		return defaultVal;
	}
	
	function getDefinedVal(val, defaultVal) {
		if ("undefined" != (typeof val)) {
			return val;
		}
		return defaultVal;
	}
	
	function endsWith(str, suffix) {
		return str.indexOf(suffix, str.length - suffix.length) !== -1;
	}
	
	function getStyleProperty(propName, element) {
		var prefixes = ['Moz', 'Webkit'];
		
		element = element || document.documentElement;
		var style = element.style, prefixed;
	
		if (typeof style[propName] == 'string') 
			return propName;
	
		propName = propName.charAt(0).toUpperCase() + propName.slice(1);
		for (var i = 0, l = prefixes.length; i < l; i++) {
		  	prefixed = prefixes[i] + propName;
		  	if (typeof style[prefixed] == 'string') {
				return prefixed;
			}
		}
	  
		return false;
	}
	
	//msie ver. check
	function msieCheck(ver) {
		if (/MSIE (\d+\.\d+);/.test(navigator.userAgent)) {
	 		var ieVer = new Number(RegExp.$1);
			if (ieVer <= ver) {
				return true;
			}
		}
		return false;
	}
	
	//shuffle array
	function shuffleArray(arr) {
		var total =  arr.length;
		for (var i = 0; i < total; i++) {
			var ri = Math.floor(Math.random() * total);
			var temp = arr[i];
			arr[i] = arr[ri];
			arr[ri] = temp;
		}	
	}
	
	//start css transition
	$.fn.cssTransition = function(props, duration, easing, delay, callback) {
		var isFn = $.isFunction(callback);
			
		return this.each(
			function() {
				if (isFn) {
					$(this).one(CSS_TRANSITION_END[TRANSITION_STYLE], callback);
				}
				$(this).css(CSS_TRANSITIONS[TRANSITION_STYLE], 'all ' + duration + 'ms ' + CUBIC_BEZIER[easing] + ' ' + delay + 'ms').css(props);
			}
		);
	}
	
	//stop css transition
	$.fn.cssTransitionStop = function(jumpToEnd) {
		return this.each(
			function() {
				if (jumpToEnd) {
					$(this).trigger(CSS_TRANSITION_END[TRANSITION_STYLE]);
				}
				$(this).css(CSS_TRANSITIONS[TRANSITION_STYLE], 'none');
			}
		);
	}
	
	$.fn.wtRotator = function(params) {
		$(this).bannerRotator(params);
	}
	
	$.fn.bannerRotator = function(params) {
		var defaults = { 
			width:'auto',
			height:'auto',			
			thumb_width:24,
			thumb_height:24,
			button_width:24,
			button_height:24,
			margin:4,
			tooltip_width:'auto',
			tooltip_height:'auto',
			background_image:'',
			background_repeat:'repeat',
			background_position:'center center',
			auto_start:true,
			delay:DEFAULT_DELAY,
			play_once:false,
			pause_onmouseover:false,
			effect:"fade",
			duration:DURATION,
			easing:"",
			block_size:BLOCK_SIZE,
			vslice_size:SLICE_SIZE,
			hslice_size:SLICE_SIZE,
			block_delay:25,
			vslice_delay:75,
			hslice_delay:75,
			cpanel_align:"BR",
			outside_cpanel:false,
			cpanel_onmouseover:false,
			thumb_type:"number",			
			select_onmouseover:false,
			tooltip_type:"text",
			tooltip_delay:0,
			dbuttons_type:"small",
			dbuttons_onmouseover:false,
			display_playbutton:true,
			display_timer:true,
			timer_align:"top",
			text_effect:"fade",
			text_duration:500,
			text_easing:'',
			text_delay:0,
			text_onmouseover:false,
			text_sync:true,
			center_image:true,			
			preload:true,			
			shuffle:false,
			mousewheel:true,
			swipe:true,
			css_transition:true
		};
		
		var opts = $.extend({}, defaults, params);
		return this.each(
			function() {
				var rotator = new Rotator($(this), opts);
			}
		);
	}
})(jQuery);