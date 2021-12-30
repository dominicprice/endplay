window.addEventListener('DOMContentLoaded', (event) => {
	// Find all elements which match method signatures
	let method_sigs = document.querySelectorAll(".py.method .sig-param .pre");

	// Loop over all elements; if they end with a comma then the
	// next element needs to start on a newline
	let needs_newline = false;
	for (const elem of method_sigs) {
		console.log(elem);
		if (needs_newline) {
			elem.classList.add("pymeth-custom-nl")
			needs_newline = false;
		}
		if (elem.innerHTML.endsWith(","))
			needs_newline = true;
	}
});