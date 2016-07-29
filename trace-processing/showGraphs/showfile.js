var numDivs = 0;

function addDiv() {

    /* An increasing id for new divs and enclosing elements */
    numDivs++;
    var output = [];

    var newDiv = document.createElement('div');
    newDiv.className = "float-border";
    newDiv.id = "div" + numDivs;

    /* Create the file input element */
    newInput = document.createElement('input');
    newInput.type = "file";
    newInput.id = "file" + numDivs;
    newInput.addEventListener('change',
			      handleFileSelect, false);
    newDiv.appendChild(newInput);

    /* Create the color selector element */
    newColorInput = document.createElement('input');
    newColorInput.type = "color";
    newColorInput.id = "color" + numDivs;
    newColorInput.value = "#008000"; /* solid green */
    newColorInput.addEventListener('change',
				   handleColorChange, false);
    newDiv.appendChild(newColorInput);

    /* Create the output pane where the file will be
     * rendered. */
    newOutput = document.createElement('output');
    newOutput.id = "output" + numDivs;
    newDiv.appendChild(newOutput);

    var mainDiv = document.getElementById("main");
    mainDiv.appendChild(newDiv);
}

function getNumberFromStringId(theString) {

    return theString.replace( /^\D+/g, '');
}

function handleColorChange(evt) {

    console.log("Color changed: " + evt.target.value);
    console.log("Target id is: " + evt.target.id);

    var numericId = getNumberFromStringId(evt.target.id);
    /* Change the border of the parent div */
    var parentDiv = document.getElementById("div" + numericId);
    parentDiv.style.borderColor = evt.target.value;
}

function handleFileSelect(evt) {
    var files = evt.target.files; // FileList object

    evtTargetId = evt.target.id;
    console.assert(evtTargetId.indexOf("file") == 0,
		   "Expecting target id of format \"fileN\", where N " +
		   "is an integer.");

    var outputId = getNumberFromStringId(evtTargetId);
    console.log("outputId is " + outputId);

    // Loop through the FileList and render image files as thumbnails.
    for (var i = 0, f; f = files[i]; i++) {

	// Only process image files.
	if (!f.type.match('image.*')) {
            continue;
	}

	var reader = new FileReader();
	var outputPane = document.getElementById('output' + outputId);

	// Closure to capture the file information.
	reader.onload = (function(theFile) {
            return function(e) {
		var output = [];
		output.push('<p><strong>', escape(theFile.name), '</strong>')

		outputPane.innerHTML = output.join('');

		// Render image
		var span = document.createElement('span');
		span.innerHTML = ['<p><img width="450px" src="', e.target.result,
				  '" title="', escape(theFile.name), '"/>'].join('');
		outputPane.insertBefore(span, null);
            };
	})(f);

	// Read in the image file as a data URL.
	reader.readAsDataURL(f);
    }
    /*  Now add another div element for selecting the file, unless we are
     * replacing the file within a div with another file previously rendered.
     */
    if(outputId == numDivs)
	addDiv();
}


document.getElementById('file0').addEventListener('change',
						  handleFileSelect, false);

document.getElementById('color0').addEventListener('change',
						  handleColorChange, false);
