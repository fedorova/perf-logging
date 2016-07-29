var numDivs = 0;

function addDiv() {

    numDivs++;
    var output = [];

    var mainDiv = document.getElementById("main");
    var newDiv = document.createElement('div');
    newDiv.className = "float";

    newInput = document.createElement('input');
    newInput.type = "file";
    newInput.id = "file" + numDivs;
    newInput.addEventListener('change',
			      handleFileSelect, false);
    newDiv.appendChild(newInput);

    newOutput = document.createElement('output');
    newOutput.id = "output" + numDivs;
    newDiv.appendChild(newOutput);

    var newBreak = document.createElement("br");
    newDiv.appendChild(newBreak);

    //document.body.appendChild(newDiv);
    mainDiv.appendChild(newDiv);
}


function handleFileSelect(evt) {
    var files = evt.target.files; // FileList object

    evtTargetId = evt.target.id;
    console.log("Triggered by " + evtTargetId);
    console.assert(evtTargetId.indexOf("file") == 0,
		   "Expecting target id of format \"fileN\", where N " +
		   "is an integer.");

    var strArray = evtTargetId.split("file");
    console.assert(strArray.length > 1,
		   "Expecting target id of format \"fileN\", where N " +
		   "is an integer.");
    var outputId = strArray[1];
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
    // Now add another div element for selecting the file.
    addDiv();
}


document.getElementById('file0').addEventListener('change',
						  handleFileSelect, false);
