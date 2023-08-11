const players = ["north", "east", "south", "west"];
const suits = ["spades", "hearts", "diamonds", "clubs"];
const denoms = [...suits, "nt"];

// e contains references to all elements on the page
const e = {};

e.sidebar = {};
e.sidebar.checkpoint = document.getElementById("checkpoint");
e.sidebar.rewind = document.getElementById("rewind");
e.sidebar.duo = document.getElementById("undo");
e.sidebar.redo = document.getElementById("redo");
e.sidebar.fastforward = document.getElementById("fastforward");
e.sidebar.output = document.getElementById("output");
e.sidebar.history = document.getElementById("history");
e.sidebar.shuffle = document.getElementById("shuffle");
e.sidebar.deal = document.getElementById("deal");
e.sidebar.board = document.getElementById("board");

e.hands = {};
for (const player of players) {
    e.hands[player] = {};
    for (const denom of suits)
        e.hands[player][denom] = document.querySelector(`#${player} .${denom}`);
}

e.trick = {};
e.first = {};
e.hcp = {};
e.tableMain = document.getElementById("ddtable");
e.table = {};
for (const player of players) {
    e.table[player] = {};
    for (const denom of denoms)
        e.table[player][denom] = document.getElementById("dd-" + player + "-" + denom);
    e.trick[player] = document.getElementById("curtrick-" + player);
    e.first[player] = document.getElementById("first-" + player);
    e.hcp[player] = document.getElementById("hcp-" + player);
}

e.trump = {};
for (const denom of denoms)
    e.trump[denom] = document.getElementById("trump-" + denom);

e.boardno = document.getElementById("boardno");
e.vul = document.getElementById("vul");
e.dealer = document.getElementById("dealer");
e.solutions = document.getElementById("solutions");

function setup_event_handlers() {
    // first buttons
    for (const player of players)
        e.first[player].addEventListener("click", () => cmd("first " + player));
    // trump buttons
    for (const denom of denoms)
        e.trump[denom].addEventListener("click", () => cmd("trump " + denom));

    e.sidebar.checkpoint.addEventListener("click", () => cmd("checkpoint"));
    e.sidebar.rewind.addEventListener("click", () => cmd("rewind"));
    e.sidebar.duo.addEventListener("click", () => cmd("undo"));
    e.sidebar.redo.addEventListener("click", () => cmd("redo"));
    e.sidebar.fastforward.addEventListener("click", () => cmd("fastforward"));

    e.sidebar.shuffle.addEventListener("click", () => {
        const constraint = prompt("Enter a constraint for the deal:");
        if (constraint)
            cmd("shuffle '" + constraint + "'");
        else
            cmd("shuffle");
    });
    e.sidebar.deal.addEventListener("click", () => {
        const pbn = prompt("Enter the PBN string to deal:");
        if (pbn !== null)
            cmd("deal '" + pbn + "'");
    });
    e.sidebar.board.addEventListener("click", () => {
        const board = prompt("Enter the board number:");
        if (board !== null)
            cmd("board '" + board + "'");
    });
}

function update({
    deal,
    hcp,
    output,
    history,
    history_idx,
    ddtable,
    solutions
}) {
    for (const player of players) {
        // update hand
        const s = deal[player].split(".");
        for (let i = 0; i < 4; ++i) {
            const denom = suits[i];
            e.hands[player][denom].innerHTML = "";
            if (s[i].length === 0) {
                e.hands[player][denom].innerText = "---";
            } else {
                for (const rank of s[i]) {
                    const card = document.createElement("span");
                    card.classList.add("card");
                    card.innerText = rank;
                    const name = denom[0] + rank;
                    card.addEventListener("click", () => cmd("play " + name));

                    if (deal.onlead === player) {
                        if (deal.legal_moves.find(c => c.suit === denom && c.rank === rank))
                            card.classList.add("legal");
                    }
                    e.hands[player][denom].appendChild(card);
                }
            }
        }

        // update first
        if (deal.first === player)
            e.first[player].classList.add("active");
        else
            e.first[player].classList.remove("active");

        // update trick
        e.trick[player].innerHTML = "";
        e.trick[player].classList.remove("spades", "hearts", "diamonds", "clubs", "card");
        const trick = deal.curtrick[player];
        if (trick) {
            e.trick[player].innerHTML = trick.rank;
            e.trick[player].classList.add(trick.suit, "card");
        }

        // update hcp
        e.hcp[player].innerText = hcp[player];
    }

    // update trump
    for (const denom of denoms) {
        if (deal.trump === denom)
            e.trump[denom].classList.add("active");
        else
            e.trump[denom].classList.remove("active");
    }

    // update board info
    e.boardno.innerText = "Board " + deal.board_no;
    e.vul.innerText = "Vul " + deal.vul;
    e.dealer.innerText = deal.dealer + " deals";

    // update history
    e.sidebar.history.innerHTML = "";
    let active = null;
    for (let i = 0; i < history.length; ++i) {
        let h = document.createElement("div");
        h.classList.add("history");
        if (history_idx === i)
            active = h;
        h.innerText = history[i];
        e.sidebar.history.appendChild(h);
    }
    active.classList.add("active");
    active.scrollIntoView();

    // update output
    e.sidebar.output.classList.remove("error");
    e.sidebar.output.innerText = output || "No message";

    // update dd table
    if (ddtable) {
        e.tableMain.classList.remove("stale");
        for (const player of players) {
            for (const denom of denoms) {
                e.table[player][denom].innerText = ddtable[player][denom];
            }
        }
    } else {
        e.tableMain.classList.add("stale");
    }

    // update solutions
    e.solutions.innerHTML = "";
    if (solutions) {
        for (const {
                suit,
                rank,
                tricks
            }
            of solutions) {
            const n = document.createElement("div");
            n.classList.add(suit);
            n.innerHTML = rank + ": " + tricks;
            e.solutions.appendChild(n);
        }
    }
}

function displayError({
    error
}) {
    e.sidebar.output.classList.add("error");
    e.sidebar.output.innerText = error;
}

async function cmd(command) {
    e.sidebar.output.classList.remove("error");
    e.sidebar.output.innerText = "loading...";
    try {
        const response = await fetch("/command", {
            method: "POST",
            body: command
        });
        const data = await response.json();
        response.ok ? update(data) : displayError(data);
    } catch (e) {
        displayError({
            error: e
        });
        return;
    }
}

setup_event_handlers();
cmd("fastforward");