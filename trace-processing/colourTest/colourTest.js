
/**
 * Initializes the shape.
 */
function Shape(x, y, w, h, fill) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;
    this.fill = fill;
}

/* Get the canvas element. */
var elem = document.getElementById('myCanvas');

function drawRectangleArray(baseHue, baseSaturation, baseLightness,
			    row_num) {

    width = 50;
    height = 50;
    padding = 5;
    var myRect = [];
    lightnessIncr = 2;

    /*
    for (i = 0; i < 14; i++) {
	myRect.push(new Shape(i * (padding + width),
			      (padding+height) * row_num, width, height,
			      'hsl(' + baseHue + ', ' + baseSaturation
			      + '%, ' + (baseLightness + lightnessIncr*i)
			      + '%)'));
    }
    */

    myRect.push(new Shape(padding + width,
			  (padding+height) * row_num, width, height,
			  'hsl(' + baseHue + ', ' + baseSaturation
			  + '%, ' + (baseLightness + lightnessIncr*row_num)
			  + '%)'));
    console.log("Hue: " + baseHue + ", Saturation: " + baseSaturation +
		", Lightness: " + (baseLightness + lightnessIncr*row_num));

    context = elem.getContext('2d');
    for (var i in myRect) {
        oRec = myRect[i];
        context.fillStyle = oRec.fill;
        context.fillRect(oRec.x, oRec.y, oRec.w, oRec.h);

    }
}

if (elem.getContext) {

    for (i = 0; i < 14; i++) {
	drawRectangleArray(360-i*20, 70, 56, i);
    }
}

