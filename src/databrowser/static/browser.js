// Behavior for pages built by databrowser: clickable table rows, filtering and sorting
// tables, the image controls and enlarged images. Every page still reads and links without it.

// Open a row's target when the row is clicked, except on a link or while selecting text.
function initRows() {
  for (const tr of document.querySelectorAll("tr[data-href]")) {
    tr.addEventListener("click", event => {
      if (event.target.closest("a") || window.getSelection().toString()) return;
      location.href = tr.dataset.href;
    });
  }
}

// Hide the rows of a table that do not contain the text typed in its filter box.
function initFilter() {
  for (const box of document.querySelectorAll(".table > .filter")) {
    const body = box.parentElement.querySelector("tbody");
    box.addEventListener("input", () => {
      const query = box.value.toLowerCase();
      for (const tr of body.rows)
        tr.hidden = !tr.textContent.toLowerCase().includes(query);
    });
  }
}

// A cell's sort key: its number when it holds one, else its text in lower case.
function sortKey(td) {
  const text = td.dataset.sort ?? td.textContent.trim();
  const number = Number(text);
  if (text !== "" && !Number.isNaN(number)) return number;
  return text.toLowerCase();
}

// Numbers sort before text, and each kind in its natural order.
function compareKeys(a, b) {
  if (typeof a !== typeof b) return typeof a === "number" ? -1 : 1;
  if (a < b) return -1;
  if (a > b) return 1;
  return 0;
}

// Sort a table by a column when its heading is clicked; a second click reverses it.
function initSort() {
  for (const table of document.querySelectorAll(".table table")) {
    const headings = [...table.tHead.rows[0].cells];
    headings.forEach((th, column) => th.addEventListener("click", () => {
      const ascending = !th.classList.contains("asc");
      headings.forEach(h => h.classList.remove("asc", "desc"));
      th.classList.add(ascending ? "asc" : "desc");
      const body = table.tBodies[0];
      const rows = [...body.rows];
      const direction = ascending ? 1 : -1;
      rows.sort((a, b) => direction * compareKeys(sortKey(a.cells[column]), sortKey(b.cells[column])));
      body.append(...rows);
    }));
  }
}

// The image width slider and caption switch, for every image on the page without a fixed size.
function initImageControls() {
  const root = document.documentElement;
  for (const controls of document.querySelectorAll(".imagecontrols")) {
    const slider = controls.querySelector(".imagewidth");
    const setWidth = () => root.style.setProperty("--image-width", slider.value + "px");
    setWidth();
    slider.addEventListener("input", setWidth);
    controls.querySelector(".captions").addEventListener("change", event =>
      root.classList.toggle("hidecaptions", !event.target.checked));
  }
}

// Show an image enlarged, with its caption, until clicked or Escape is pressed. An image in
// a clickable table row opens the row's target instead.
function initLightbox() {
  const box = document.querySelector(".lightbox");
  for (const img of document.querySelectorAll("figure.image img")) {
    if (img.closest("tr[data-href]")) continue;
    img.addEventListener("click", () => {
      box.querySelector("img").src = img.src;
      const caption = img.parentElement.querySelector("figcaption");
      box.querySelector("div").innerHTML = caption ? caption.innerHTML : "";
      box.classList.add("open");
    });
  }
  box.addEventListener("click", () => box.classList.remove("open"));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") box.classList.remove("open");
  });
}

initRows();
initFilter();
initSort();
initImageControls();
initLightbox();
