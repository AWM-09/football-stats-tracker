let COMPETITIONS = [];
const GROUPS = ["Leagues", "UEFA Competitions", "International Football", "Domestic Cups"];
const FILTERS = ["All", ...GROUPS];
const TABS = ["Overview", "Standings", "Fixtures & Results", "Teams", "Players", "Head to Head", "Records"];
const VIEW_TITLES = {teams:"Teams",players:"Players",calendar:"Calendar",records:"Records"};
const DATA_MESSAGE = "Open-data coverage varies by competition and season. OpenPlay adds historical player and team totals through 2025/26; missing fields are shown as unavailable rather than estimated.";
const PREMIER_LEAGUE_TEAM_DETAILS={
  arsenal:{founded:1886,stadium:"Emirates Stadium",capacity:60704},
  "aston-villa":{founded:1874,stadium:"Villa Park",capacity:36887},
  bournemouth:{founded:1899,stadium:"Vitality Stadium",capacity:12357},
  brentford:{founded:1889,stadium:"Gtech Community Stadium",capacity:17250},
  brighton:{founded:1901,stadium:"American Express Stadium",capacity:32176},
  chelsea:{founded:1905,stadium:"Stamford Bridge",capacity:40044},
  coventry:{founded:1883,stadium:"Coventry Building Society Arena",capacity:32609},
  "crystal-palace":{founded:1905,stadium:"Selhurst Park",capacity:25194},
  everton:{founded:1878,stadium:"Hill Dickinson Stadium",capacity:52769},
  fulham:{founded:1879,stadium:"Craven Cottage",capacity:28107},
  hull:{founded:1904,stadium:"MKM Stadium",capacity:24983},
  ipswich:{founded:1878,stadium:"Portman Road",capacity:30294},
  leeds:{founded:1919,stadium:"Elland Road",capacity:37633},
  liverpool:{founded:1892,stadium:"Anfield",capacity:61276},
  "man-city":{founded:1880,stadium:"Etihad Stadium",capacity:61038},
  "man-utd":{founded:1878,stadium:"Old Trafford",capacity:74158},
  newcastle:{founded:1892,stadium:"St James’ Park",capacity:52729},
  "nott-m-forest":{founded:1865,stadium:"The City Ground",capacity:31212},
  sunderland:{founded:1879,stadium:"Stadium of Light",capacity:48095},
  spurs:{founded:1882,stadium:"Tottenham Hotspur Stadium",capacity:62850}
};

function byId(id){return document.getElementById(id)}
function esc(value){return String(value).replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]))}
async function fetchSnapshot(path){
  const suffix="?v="+Date.now();
  try{
    const compressed=await fetch(path+".gz"+suffix);
    if(compressed.ok&&"DecompressionStream" in window){
      return await new Response(compressed.body.pipeThrough(new DecompressionStream("gzip"))).json();
    }
  }catch{}
  const response=await fetch(path+suffix);
  return response.ok?response.json():null;
}
function competitionUrl(item){return `./competition.html?id=${encodeURIComponent(item.id)}`}
function renderCard(item){return `<a class="competition-card" href="${competitionUrl(item)}" style="--card-accent:${esc(item.accent)}"><div class="card-top"><span class="competition-badge" aria-hidden="true">${esc(item.code)}</span><span class="card-category">${esc(item.kind)}</span><span class="card-arrow" aria-hidden="true">↗</span></div><h3>${esc(item.name)}</h3><p class="card-detail">${esc(item.country)} <span>·</span> ${esc(item.season)}</p><p class="card-description">${esc(item.description)}</p></a>`}

function initDirectory(){
  const root=byId("competitionGroups");
  if(!root)return;
  let active="All",query="";
  const filters=byId("filterRow"),search=byId("competitionSearch"),empty=byId("emptyState");
  filters.innerHTML=FILTERS.map((name,i)=>`<button class="filter-chip${i===0?" active":""}" type="button" aria-pressed="${i===0}" data-filter="${esc(name)}">${esc(name)}</button>`).join("");
  function draw(){
    const matches=COMPETITIONS.filter(item=>(active==="All"||item.group===active)&&`${item.name} ${item.country} ${item.kind}`.toLowerCase().includes(query));
    root.innerHTML=GROUPS.map(group=>{const items=matches.filter(item=>item.group===group);if(!items.length)return "";const desc=group==="Leagues"?"Six top-flight leagues from the countries in your plan.":group==="UEFA Competitions"?"The three major UEFA club competitions.":group==="International Football"?"Major national-team tournaments and qualification.":"English and Polish domestic cups and super cups.";return `<section class="competition-group"><div class="section-heading group-heading"><div><h2>${esc(group)}</h2><p>${esc(desc)}</p></div><span class="count-pill">${items.length} ${items.length===1?"competition":"competitions"}</span></div><div class="competition-grid">${items.map(renderCard).join("")}</div></section>`}).join("");
    empty.hidden=matches.length>0;
  }
  filters.addEventListener("click",event=>{const btn=event.target.closest("[data-filter]");if(!btn)return;active=btn.dataset.filter;filters.querySelectorAll(".filter-chip").forEach(chip=>{const selected=chip===btn;chip.classList.toggle("active",selected);chip.setAttribute("aria-pressed",String(selected))});draw()});
  search.addEventListener("input",()=>{query=search.value.trim().toLowerCase();draw()});
  draw();
}

function initCompetitionPage(){
  const hero=byId("competitionHero"),panel=byId("competitionPanel"),tabs=byId("competitionTabs");
  if(!hero||!panel||!tabs)return;
  const params=new URLSearchParams(location.search),id=params.get("id"),view=params.get("view"),item=COMPETITIONS.find(comp=>comp.id===id);
  if(!item){
    const title=VIEW_TITLES[view];
    if(title){tabs.innerHTML="";byId("leagueHomeShell").hidden=true;byId("competitionContent").hidden=false;initGlobalView(view,hero,panel);return}
    hero.innerHTML=`<div class="eyebrow">Competition not found</div><h1 class="title">Choose a <span>competition.</span></h1><a class="button-link" href="./index.html">Browse competitions →</a>`;
    tabs.innerHTML="";panel.innerHTML=`<div class="unavailable"><span class="unavailable-icon">◷</span><h2>Competition not found</h2><p>Choose a competition from the directory.</p><a class="text-link" href="./index.html">Browse competitions →</a></div>`;return;
  }
  document.title=`${item.name} | Football/Soccer Analytics`;
  const requestedTab=String(params.get("tab")||"").toLowerCase(),initialTab=TABS.find(name=>name.toLowerCase()===requestedTab)||"Overview";
  tabs.innerHTML=TABS.map(name=>`<button class="tab-button${name===initialTab?" active":""}" role="tab" aria-selected="${name===initialTab}" data-tab="${esc(name)}">${esc(name)}</button>`).join("");
  const homeShell=byId("leagueHomeShell"),competitionContent=byId("competitionContent");
  const showToolView=params.has("tab")&&initialTab!=="Overview";
  if(homeShell)homeShell.hidden=showToolView;
  if(competitionContent)competitionContent.hidden=!showToolView;
  const currentYear=Number(String(item.season).slice(0,4));
  let selectedSeason=params.get("season")||String(currentYear),activeTab=initialTab,snapshot=null,coverage=null;
  const tools=byId("competitionTools"),nav=byId("competitionNav"),features=byId("competitionFeatures");
  function renderCompetitionTools(){
    if(!tools)return;
    const tabHref=tab=>`./competition.html?id=${encodeURIComponent(item.id)}&season=${encodeURIComponent(selectedSeason)}&tab=${encodeURIComponent(tab)}`;
    const statHref=`./stats.html?competition=${encodeURIComponent(item.id)}&season=${encodeURIComponent(selectedSeason)}`;
    const cards=[
      ["📊","Core statistics",`${item.name} Stats`,"Weekly leaders, season totals, team comparisons, trends and statistical records.",statHref],
      ["⚽","Player database","Player Profiles","Search league players, review season totals and open individual profiles.",tabHref("Players")],
      ["🏟️","Team database","Team Platform","Explore clubs, team statistics, results and season performance.",tabHref("Teams")],
      ["🏆","League table","Standings & Groups","Review points, wins, draws, losses, goal difference and group positions.",tabHref("Standings")],
      ["🗓️","Match centre","Calendar & Results","Search fixtures by club or round and open the published match details.",tabHref("Fixtures & Results")],
      ["⚔️","Matchups","Head to Head","Compare clubs across their meetings in the selected season.",tabHref("Head to Head")],
      ["📈","Season records","Records & Milestones","Explore highest scoring matches, largest margins and top scorers.",tabHref("Records")],
      ["🛠️","Reliability","Data Status","Review source coverage, refresh times and available statistics.",`./health.html?competition=${encodeURIComponent(item.id)}`]
    ];
    tools.innerHTML=cards.map(([icon,category,title,description,href])=>`<a class="tool" href="${href}"><div class="tool-top"><span class="iconbox">${icon}</span><span class="tag">${esc(category)}</span><span class="arrow">↗</span></div><h3>${esc(title)}</h3><p>${esc(description)}</p></a>`).join("");
  }
  const table=(headers,rows,emptyText="No rows are available for this section yet.")=>rows&&rows.length?`<div class="table-scroll"><table class="data-table"><thead><tr>${headers.map(h=>`<th>${esc(h.label)}</th>`).join("")}</tr></thead><tbody>${rows.map(row=>`<tr>${headers.map(h=>`<td>${h.render? h.render(row):esc(row[h.key]??"—")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`:`<div class="data-empty"><span class="unavailable-icon">◷</span><h3>${esc(emptyText)}</h3><p>This section is unavailable in the published open dataset for this competition and season.</p></div>`;
  const nameLink=(name,type,entityId)=>entityId?`<a class="data-link" href="./entity.html?type=${type}&id=${encodeURIComponent(entityId)}&competition=${encodeURIComponent(item.id)}&season=${encodeURIComponent(selectedSeason)}">${esc(name||"Unknown")}</a>`:esc(name||"Unknown");
  const sourceState=group=>snapshot?.coverage?.[group];
  const sectionHead=(title,group)=>{const meta=sourceState(group);return `<div class="panel-heading"><div><div class="eyebrow">${esc(item.name)} · ${esc(snapshot?.seasonLabel||item.season)}</div><h2>${esc(title)}</h2></div><span class="availability-pill ${meta?.available?"is-ready":""}"><i class="status-dot ${meta?.available?"good":"pending"}"></i>${meta?.available?`${Number(meta.rows||0).toLocaleString()} rows · ${esc((meta.fetchedAt||"").replace("T"," ").replace("Z"," UTC"))}`:"Not available"}</span></div>`};
  function render(tab){
    const titles={"Overview":"Competition overview","Standings":"Standings & table","Fixtures & Results":"Fixtures & results","Teams":"Teams","Players":"Players","Records":"Competition records"};
    if(!snapshot){panel.innerHTML=`${sectionHead(titles[tab]||tab,tab=== "Overview"?"fixtures":tabKey(tab))}<div class="unavailable"><span class="unavailable-icon">◷</span><h3>No open-data snapshot for this season</h3><p>${esc(DATA_MESSAGE)} See the Data Status page for source coverage and refresh details.</p><a class="text-link" href="./health.html">Check data status →</a></div>`;return}
    if(tab==="Overview"){
      const played=(snapshot.fixtures||[]).filter(f=>["FT","AET","PEN"].includes(f.status)).length;
      const cards=[[
        "Clubs / teams",snapshot.teams?.length??"—"], ["Matches in season",snapshot.fixtures?.length??"—"], ["Completed",played], ["Players in snapshot",snapshot.players?.length??"—"]
      ];
      const upcoming=(snapshot.fixtures||[]).filter(f=>!(["FT","AET","PEN","CANC","ABD","AWD","WO"].includes(f.status))).slice(0,6);
      const recent=(snapshot.fixtures||[]).filter(f=>["FT","AET","PEN"].includes(f.status)).slice(-6).reverse();
      panel.innerHTML=`${sectionHead(titles[tab],"fixtures")}<div class="metric-grid">${cards.map(([label,value])=>`<article class="metric-card"><span>${esc(label)}</span><strong>${esc(value)}</strong></article>`).join("")}</div><div class="overview-grid"><section class="data-subpanel"><h3>Latest results</h3>${fixturesTable(recent)}</section><section class="data-subpanel"><h3>Upcoming fixtures</h3>${fixturesTable(upcoming)}</section></div><p class="source-note">Source: ${esc(snapshot.provider||"Source unavailable")} · refreshed ${esc(snapshot.generatedAt||"unknown")} · values are shown only when supplied by the source.</p>`;
    } else if(tab==="Standings"){
      const rows=snapshot.standings||[];
      const columns=[...(rows.some(row=>row.group)?[{label:"Group",key:"group"}]:[]),{label:"#",key:"rank"},{label:"Team",render:r=>nameLink(r.team,"team",r.teamId)},{label:"P",key:"played"},{label:"W",key:"won"},{label:"D",key:"drawn"},{label:"L",key:"lost"},{label:"GF",key:"goalsFor"},{label:"GA",key:"goalsAgainst"},{label:"GD",key:"goalDifference"},{label:"Pts",key:"points"},{label:"Form",key:"form"}];
      panel.innerHTML=`${sectionHead(titles[tab],"standings")}${table(columns,rows,"No standings supplied")}`;
    } else if(tab==="Fixtures & Results"){
      const rows=snapshot.fixtures||[];
      panel.innerHTML=`${sectionHead(titles[tab],"fixtures")}<label class="table-search"><span>Find a team or round</span><input id="rowSearch" type="search" placeholder="Search fixtures"></label><div id="fixturesTable">${fixturesTable(rows)}</div>`;
      byId("rowSearch")?.addEventListener("input",event=>{const q=event.target.value.toLowerCase();byId("fixturesTable").innerHTML=fixturesTable(rows.filter(f=>`${f.home?.name} ${f.away?.name} ${f.round} ${f.statusLong}`.toLowerCase().includes(q)))})
    } else if(tab==="Teams"){
      const rows=snapshot.teams||[];
      panel.innerHTML=`${sectionHead(titles[tab],"teams")}<label class="table-search"><span>Find a team</span><input id="rowSearch" type="search" placeholder="Search teams"></label><div id="teamsTable">${teamsTable(rows)}</div>`;
      byId("rowSearch")?.addEventListener("input",event=>{const q=event.target.value.toLowerCase();byId("teamsTable").innerHTML=teamsTable(rows.filter(r=>`${r.name} ${r.country} ${r.venue?.name||PREMIER_LEAGUE_TEAM_DETAILS[r.id]?.stadium||""}`.toLowerCase().includes(q)))});
      if(item.id==="premier-league")panel.insertAdjacentHTML("beforeend",`<p class="source-note">Stadiums and 2026/27 capacities: <a href="https://www.premierleague.com/en/news/4725666/all-you-need-to-know-about-the-20-premier-league-stadiums/" target="_blank" rel="noopener">Premier League stadium guide</a>. Founded years are club establishment years.</p>`)
    } else if(tab==="Players"){
      const rows=snapshot.players?.length?snapshot.players:(snapshot.topScorers||[]);
      panel.innerHTML=`${sectionHead(titles[tab],"players")}<label class="table-search"><span>Find a player</span><input id="rowSearch" type="search" placeholder="Search player, club or position"></label><div id="playersTable">${playersTable(rows)}</div>`;
      byId("rowSearch")?.addEventListener("input",event=>{const q=event.target.value.toLowerCase();byId("playersTable").innerHTML=playersTable(rows.filter(r=>`${r.name} ${r.team} ${r.position} ${r.nationality}`.toLowerCase().includes(q)))})
    } else if(tab==="Head to Head"){
      const teams=snapshot.teams||[],fixtures=snapshot.fixtures||[];
      panel.innerHTML=`${sectionHead(titles[tab]||tab,"fixtures")}<div class="compare-controls"><label>Home team<select id="h2hHome">${teams.map(t=>`<option value="${esc(t.id)}">${esc(t.name)}</option>`).join("")}</select></label><label>Away team<select id="h2hAway">${teams.map((t,i)=>`<option value="${esc(t.id)}" ${i===1?"selected":""}>${esc(t.name)}</option>`).join("")}</select></label></div><div id="h2hResult"></div>`;
      const update=()=>{const home=byId("h2hHome")?.value,away=byId("h2hAway")?.value;const matches=fixtures.filter(f=>[`${f.home?.id}-${f.away?.id}`,`${f.away?.id}-${f.home?.id}`].includes(`${home}-${away}`));byId("h2hResult").innerHTML=renderH2H(matches,home,away,teams)};
      byId("h2hHome")?.addEventListener("change",update);byId("h2hAway")?.addEventListener("change",update);update();
    } else {
      panel.innerHTML=`${sectionHead(titles[tab],"fixtures")}<div class="record-grid">${recordCards(snapshot,item,selectedSeason)}</div>`
    }
  }
  function tabKey(tab){return ({"Standings":"standings","Fixtures & Results":"fixtures","Teams":"teams","Players":"players","Records":"fixtures"})[tab]||"fixtures"}
  function fixturesTable(rows){const columns=[{label:"Date",render:r=>esc(formatDate(r.date))},{label:"Round",key:"round"},...(rows.some(row=>row.group)?[{label:"Group",key:"group"}]:[]),{label:"Home",render:r=>nameLink(r.home?.name,"team",r.home?.id)},{label:"Score",render:r=>`<a class="data-link" href="./match.html?id=${encodeURIComponent(r.id)}&competition=${encodeURIComponent(item.id)}&season=${encodeURIComponent(selectedSeason)}"><strong>${scoreText(r)}</strong></a>`},{label:"Away",render:r=>nameLink(r.away?.name,"team",r.away?.id)},{label:"Status",render:r=>esc(r.statusLong||r.status||"—")}];return table(columns,rows,"No fixture rows supplied")}
  function teamsTable(rows){const enriched=rows.map(r=>{const profile=item.id==="premier-league"?PREMIER_LEAGUE_TEAM_DETAILS[r.id]||{}:{};return{...r,founded:r.founded??profile.founded,stadium:r.venue?.name||profile.stadium,capacity:r.venue?.capacity??profile.capacity}});return table([{label:"Team",render:r=>`<span class="team-cell">${r.logo?`<img loading="lazy" src="${esc(r.logo)}" alt="">`:""}${nameLink(r.name,"team",r.id)}</span>`},{label:"Country",key:"country"},{label:"Founded",render:r=>esc(r.founded??"—")},{label:"Stadium",render:r=>esc(r.stadium||"—")},{label:"Capacity",render:r=>esc(r.capacity==null?"—":Number(r.capacity).toLocaleString())}],enriched,"No team list supplied") }
  function playersTable(rows){return table([{label:"Player",render:r=>`<span class="player-cell">${r.photo?`<img loading="lazy" src="${esc(r.photo)}" alt="">`:""}${nameLink(r.name,"player",r.id)}</span>`},{label:"Club",key:"team"},{label:"Pos",key:"position"},{label:"Apps",key:"appearances"},{label:"Mins",key:"minutes"},{label:"Goals",key:"goals"},{label:"Assists",key:"assists"},{label:"xG",key:"expectedGoals"},{label:"xA",key:"expectedAssists"},{label:"Shots",key:"shots"},{label:"Shots on target",key:"shotsOnTarget"},{label:"Chances created",key:"chancesCreated"},{label:"Passes completed",key:"passesCompleted"},{label:"Tackles",key:"tackles"},{label:"Interceptions",key:"interceptions"},{label:"Clearances",key:"clearances"},{label:"Saves",key:"saves"},{label:"Y/R",render:r=>esc(`${r.yellow_cards??r.yellowCards??"—"}/${r.red_cards??r.redCards??"—"}`)}],rows,"No player statistics supplied")}
  function formatDate(value){if(!value)return"—";const d=new Date(value);return Number.isNaN(d.valueOf())?value:new Intl.DateTimeFormat(undefined,{dateStyle:"medium",timeStyle:"short"}).format(d)}
  function scoreText(f){return f.goals?.home==null||f.goals?.away==null?"—":`${f.goals.home} – ${f.goals.away}`}
  function recordCards(data,comp,season){
    const finished=(data.fixtures||[]).filter(f=>["FT","AET","PEN"].includes(f.status)&&Number.isFinite(f.goals?.home)&&Number.isFinite(f.goals?.away));
    const maxGoal=finished.reduce((best,f)=>(f.goals.home+f.goals.away)>(best?.goals.home+best?.goals.away||-1)?f:best,null);
    const biggest=finished.reduce((best,f)=>Math.abs(f.goals.home-f.goals.away)>Math.abs(best?.goals.home-best?.goals.away||0)?f:best,null);
    const top=(data.topScorers||[]).slice(0,5);
    const items=[["Most goals in a match",maxGoal?`${maxGoal.home.name} ${scoreText(maxGoal)} ${maxGoal.away.name}`:"Unavailable",maxGoal?`${formatDate(maxGoal.date)} · source match data`:"No completed match scores supplied"],["Largest score margin",biggest?`${biggest.home.name} ${scoreText(biggest)} ${biggest.away.name}`:"Unavailable",biggest?`${formatDate(biggest.date)} · source match data`:"No completed match scores supplied"],["Top scorer",top[0]?.name||"Unavailable",top[0]?`${top[0].goals??"—"} goals · ${top[0].team||"team not supplied"}`:"No scorer leaderboard supplied"]];
    return items.map(([label,value,detail])=>`<article class="record-card"><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(detail)} · ${esc(comp.name)} ${esc(season)}</small></article>`).join("")
  }
  async function load(){
    try{const r=await fetch("./data/coverage.json?v="+Date.now());coverage=r.ok?await r.json():null}catch{coverage=null}
    const seasons=[...new Set((coverage?.competitions?.[item.id]?.seasons||[]).map(String))].sort((a,b)=>Number(b.slice(0,4))-Number(a.slice(0,4)));
    if(!seasons.length)seasons.push(String(currentYear));
    const selected=seasons.includes(String(selectedSeason))?String(selectedSeason):(seasons.includes(String(currentYear))?String(currentYear):seasons[0]);selectedSeason=selected;
    const labelFor=year=>year===String(currentYear)?item.season:(coverage?.competitions?.[item.id]?.seasonLabels?.[year]||year);
    const tabHref=tab=>`./competition.html?id=${encodeURIComponent(item.id)}&season=${encodeURIComponent(selectedSeason)}&tab=${encodeURIComponent(tab)}`;
    const statHref=`./stats.html?competition=${encodeURIComponent(item.id)}&season=${encodeURIComponent(selectedSeason)}`;
    renderCompetitionTools();
    if(nav)nav.innerHTML=[
      ["Stats Tracker",statHref],["Players",tabHref("Players")],["Teams",tabHref("Teams")],["Standings",tabHref("Standings")],["Match Centre",tabHref("Fixtures & Results")],["Records",tabHref("Records")],["Data Status",`./health.html?competition=${encodeURIComponent(item.id)}`]
    ].map(([label,href])=>`<a href="${href}">${esc(label)}</a>`).join("");
    if(features)features.innerHTML=`<a class="feature" href="${tabHref("Standings")}"><h3>${esc(item.name)} table and form ↗</h3><p>Review positions, points, recent results and the teams shaping this season.</p></a><a class="feature" href="./health.html?competition=${encodeURIComponent(item.id)}"><h3>Transparent data coverage ↗</h3><p>See which seasons and statistics are available, when data was refreshed, and where gaps remain.</p></a>`;
    hero.innerHTML=`<div class="eyebrow">${esc(item.name)} data workspace</div><h1 class="title">Understand the game.<br><span>Beyond the table.</span></h1><p class="sub">Explore ${esc(item.name)} standings, player performances, club statistics, match data and season records in one connected Football/Soccer workspace.</p><div class="hero-actions"><a class="button primary" href="${statHref}">Open ${esc(item.name)} Stats ↗</a><a class="button" href="${tabHref("Players")}">Explore Player Profiles ↗</a><a class="button" href="${tabHref("Fixtures & Results")}">Open Match Centre ↗</a></div><div class="hero-meta"><span class="status-dot pending" id="heroSnapshotDot"></span><span id="heroSnapshotLabel">${esc(labelFor(selectedSeason))} data snapshot</span><span class="meta-sep">·</span><label class="home-season" for="seasonSelect">Season<select id="seasonSelect">${seasons.map(year=>`<option value="${esc(year)}" ${year===selected?"selected":""}>${esc(labelFor(year))}</option>`).join("")}</select></label></div>`;
    const path=`./data/competitions/${encodeURIComponent(item.id)}-${encodeURIComponent(selectedSeason)}.json`;
    try{snapshot=await fetchSnapshot(path)}catch{snapshot=null}
    const healthDot=byId("healthDot"),healthLabel=byId("healthLabel"),healthDetail=byId("healthDetail"),heroDot=byId("heroSnapshotDot"),heroLabel=byId("heroSnapshotLabel");
    if(snapshot){healthDot?.classList.add("good");healthDot?.classList.remove("bad");if(healthLabel)healthLabel.textContent="Published data available";if(healthDetail)healthDetail.textContent=`${esc(labelFor(selectedSeason))} · ${Number(snapshot.fixtures?.length||0).toLocaleString()} fixtures · ${snapshot.provider||"Open data"}`;heroDot?.classList.add("good");heroDot?.classList.remove("pending");if(heroLabel)heroLabel.textContent=`${labelFor(selectedSeason)} data snapshot available`;}
    else{healthDot?.classList.add("bad");if(healthLabel)healthLabel.textContent="Data snapshot unavailable";if(healthDetail)healthDetail.textContent=`No published snapshot for ${labelFor(selectedSeason)}.`;heroDot?.classList.remove("good");heroDot?.classList.add("pending");if(heroLabel)heroLabel.textContent=`${labelFor(selectedSeason)} data snapshot unavailable`;}
    const healthLink=byId("healthLink");if(healthLink)healthLink.href=`./health.html?competition=${encodeURIComponent(item.id)}`;
    hero.querySelector("#seasonSelect")?.addEventListener("change",async event=>{selectedSeason=event.target.value;const next=new URL(location.href);next.searchParams.set("season",selectedSeason);history.replaceState({},"",next);await load();render(activeTab)});
    render(activeTab);
    if(params.has("tab")&&activeTab!=="Overview")requestAnimationFrame(()=>document.querySelector(".competition-content")?.scrollIntoView({block:"start",behavior:"smooth"}));
  }
  tabs.addEventListener("click",event=>{const btn=event.target.closest("[data-tab]");if(!btn)return;activeTab=btn.dataset.tab;if(homeShell)homeShell.hidden=true;if(competitionContent)competitionContent.hidden=false;const next=new URL(location.href);next.searchParams.set("tab",activeTab);history.replaceState({},"",next);tabs.querySelectorAll(".tab-button").forEach(tab=>{const selected=tab===btn;tab.classList.toggle("active",selected);tab.setAttribute("aria-selected",String(selected))});render(activeTab)});
  load();
}

async function initGlobalView(view,hero,panel){
  const title=VIEW_TITLES[view];
  hero.innerHTML=`<div class="eyebrow">Football statistics directory</div><h1 class="title">${esc(title)} <span>hub.</span></h1><p class="subtitle">Search data across the competition snapshots that have been published so far.</p><a class="button-link" href="./index.html">Choose a competition →</a>`;
  panel.innerHTML=`<div class="unavailable"><span class="unavailable-icon">◷</span><h2>Loading published snapshots</h2><p>Reading competition data.</p></div>`;
  let index={};try{const res=await fetch("./data/coverage.json");if(res.ok)index=(await res.json()).competitions||{}}catch{}
  const refs=COMPETITIONS.flatMap(item=>(index[item.id]?.seasons||[]).map(season=>({item,season:String(season)})));
  const snapshots=await Promise.all(refs.map(async ({item,season})=>{try{const data=await fetchSnapshot(`./data/competitions/${encodeURIComponent(item.id)}-${encodeURIComponent(season)}.json`);return data?{item,season,data}:null}catch{return null}}));
  const available=snapshots.filter(Boolean);
  if(!available.length){panel.innerHTML=`<div class="unavailable"><span class="unavailable-icon">◷</span><h2>No published open-data snapshots yet</h2><p>${esc(DATA_MESSAGE)} The static data workflow refreshes supported files daily.</p><a class="text-link" href="./health.html">Check data status →</a></div>`;return}
  const searchBar=`<label class="table-search"><span>Search ${esc(title.toLowerCase())}</span><input id="globalSearch" type="search" placeholder="Search ${esc(title.toLowerCase())}"></label>`;
  let rows=[];
  if(view==="teams")rows=available.flatMap(({item,season,data})=>(data.teams||[]).map(team=>({...team,competition:item.name,competitionId:item.id,season})));
  else if(view==="players")rows=available.flatMap(({item,season,data})=>(data.players||data.topScorers||[]).map(player=>({...player,competition:item.name,competitionId:item.id,season})));
  else if(view==="calendar")rows=available.flatMap(({item,season,data})=>(data.fixtures||[]).map(f=>({...f,competition:item.name,competitionId:item.id,season}))).sort((a,b)=>String(a.date||"").localeCompare(String(b.date||"")));
  else rows=available.flatMap(({item,season,data})=>recordRows(data,item,season));
  const unique=rows.filter((row,index)=>rows.findIndex(other=>view==="players"?String(row.id)===String(other.id):view==="teams"?String(row.id)===String(other.id):view==="calendar"?String(row.id)===String(other.id):`${row.competitionId}-${row.label}`===`${other.competitionId}-${other.label}` )===index);
  panel.innerHTML=`<div class="panel-heading"><div><div class="eyebrow">${available.length} competition-season snapshots</div><h2>${esc(title)}</h2></div><span class="availability-pill is-ready"><i class="status-dot good"></i>${unique.length.toLocaleString()} rows</span></div>${searchBar}<div id="globalRows">${renderGlobalRows(view,unique)}</div>`;
  byId("globalSearch")?.addEventListener("input",event=>{const q=event.target.value.toLowerCase();byId("globalRows").innerHTML=renderGlobalRows(view,unique.filter(r=>JSON.stringify(r).toLowerCase().includes(q)))})
}

async function initEntityPage(){
  const hero=byId("entityHero"),panel=byId("entityPanel");if(!hero||!panel)return;
  const params=new URLSearchParams(location.search),type=params.get("type"),id=params.get("id"),compId=params.get("competition"),item=COMPETITIONS.find(c=>c.id===compId),season=params.get("season")||String(item?.season||"").slice(0,4);
  if(!item||!id||!["player","team"].includes(type)){hero.innerHTML=`<div class="eyebrow">Profile not found</div><h1 class="title">Choose a <span>competition.</span></h1><a class="button-link" href="./index.html">Browse competitions →</a>`;panel.innerHTML=`<div class="data-empty">Select a player or team from a competition hub.</div>`;return}
  byId("entityBack").href=`./competition.html?id=${encodeURIComponent(item.id)}&season=${encodeURIComponent(season)}`;
  let coverage={};try{const r=await fetch("./data/coverage.json");if(r.ok)coverage=(await r.json()).competitions?.[item.id]||{}}catch{}
  const years=[...new Set([season,...(coverage.seasons||[]).map(String)])].sort((a,b)=>Number(b.slice(0,4))-Number(a.slice(0,4)));
  const snapshots=await Promise.all(years.map(async year=>{try{return await fetchSnapshot(`./data/competitions/${encodeURIComponent(item.id)}-${encodeURIComponent(year)}.json`)}catch{return null}}));
  const requestedSnapshot=snapshots.find(snap=>snap&&String(snap.season).slice(0,4)===String(season))||snapshots.find(Boolean);
  const requestedTeam=requestedSnapshot?.teams?.find(team=>String(team.id)===String(id));
  const found=[];
  for(const snap of snapshots.filter(Boolean)){
    if(type==="player"){
      const row=(snap.players||[]).find(p=>String(p.id)===String(id))||(snap.topScorers||[]).find(p=>String(p.id)===String(id));if(row)found.push({year:String(snap.season).slice(0,4),season:snap.seasonLabel||String(snap.season),data:row,snapshot:snap});
    }else{
      const row=(snap.teams||[]).find(t=>String(t.id)===String(id))||(requestedTeam&&(snap.teams||[]).find(t=>String(t.name||"").trim().toLowerCase()===String(requestedTeam.name||"").trim().toLowerCase()));if(row)found.push({year:String(snap.season).slice(0,4),season:snap.seasonLabel||String(snap.season),data:row,snapshot:snap,stats:snap.teamStats?.[String(row.id)]||snap.teamStats?.[String(id)]});
    }
  }
  const current=found.find(r=>String(r.snapshot.season)===String(season))||found[0];
  if(!current){hero.innerHTML=`<div class="eyebrow">${esc(item.name)} · ${esc(season)}</div><h1 class="title">${type==="player"?"Player":"Team"} profile <span>unavailable.</span></h1>`;panel.innerHTML=`<div class="unavailable"><span class="unavailable-icon">◷</span><h2>No profile data in this snapshot</h2><p>The source has not supplied this ${esc(type)} for ${esc(item.name)} in ${esc(season)}.</p><a class="text-link" href="./competition.html?id=${encodeURIComponent(item.id)}">Return to competition →</a></div>`;return}
  const profile=current.data,availableRows=found.filter(r=>type==="player"?r.data.appearances!=null||r.data.goals!=null:!!r.stats),allTime=params.get("allTime")==="1",requestedYears=(params.get("seasons")||season).split(",").filter(Boolean),selectedYears=new Set(allTime?availableRows.map(r=>r.year):requestedYears),statRows=availableRows.filter(r=>selectedYears.has(r.year));
  const sums=keys=>keys.map(([label,key])=>{const vals=statRows.map(r=>type==="player"?r.data[key]:r.stats?.[key]).filter(v=>v!==null&&v!==undefined&&Number.isFinite(Number(v))).map(Number);return {label,value:vals.length?vals.reduce((a,b)=>a+b,0):"—"}});
  const teamStatValue=(stats,key)=>({fixtures:stats?.fixtures?.played,wins:stats?.fixtures?.wins,draws:stats?.fixtures?.draws,loses:stats?.fixtures?.loses,goalsFor:stats?.goals?.for?.total,goalsAgainst:stats?.goals?.against?.total,cleanSheet:stats?.clean_sheet?.total,shots:stats?.shots,xg:stats?.xg,passes:stats?.passes,tackles:stats?.tackles,interceptions:stats?.interceptions})[key];
  const metrics=type==="player"?sums([["Apps","appearances"],["Minutes","minutes"],["Goals","goals"],["Assists","assists"],["xG","expectedGoals"],["xA","expectedAssists"],["Shots","shots"],["Shots on target","shotsOnTarget"],["Key passes","keyPasses"],["Tackles","tackles"],["Interceptions","interceptions"]]):[["Matches played","fixtures"],["Wins","wins"],["Draws","draws"],["Losses","loses"],["Goals for","goalsFor"],["Goals against","goalsAgainst"],["Clean sheets","cleanSheet"],["Shots","shots"],["xG","xg"],["Passes","passes"],["Tackles","tackles"],["Interceptions","interceptions"]].map(([label,key])=>{const values=statRows.map(r=>teamStatValue(r.stats,key)).filter(v=>v!==null&&v!==undefined&&Number.isFinite(Number(v))).map(Number);return {label,value:values.length?values.reduce((a,b)=>a+b,0):"—"}});
  hero.innerHTML=`<div class="competition-kicker"><span>${esc(item.name)}</span><span>·</span><span>${esc(current.season)}</span></div><div class="competition-title-row">${type==="player"&&profile.photo?`<img class="profile-photo" src="${esc(profile.photo)}" alt="${esc(profile.name)}">`:profile.logo?`<img class="profile-photo team-photo" src="${esc(profile.logo)}" alt="">`:``}<div><h1>${esc(profile.name)}</h1><p>${esc(type==="player"?[profile.position,profile.team,profile.nationality].filter(Boolean).join(" · "): [profile.country,profile.venue?.name].filter(Boolean).join(" · "))}</p></div></div><div class="season-row"><span class="availability-pill is-ready"><i class="status-dot good"></i>${found.length} season${found.length===1?"":"s"} with published data</span><a class="text-link" href="./competition.html?id=${encodeURIComponent(item.id)}&season=${encodeURIComponent(season)}">Back to ${esc(item.name)} →</a></div>`;
  const seasonControl='<fieldset class="season-selector"><legend>Select seasons</legend><label class="season-option"><input id="profileAllTime" type="checkbox" '+(allTime?'checked':'')+'> All time</label><div class="season-options">'+availableRows.map(r=>'<label class="season-option"><input type="checkbox" data-profile-season="'+esc(r.year)+'" '+(selectedYears.has(r.year)?'checked':'')+' '+(allTime?'disabled':'')+'> '+esc(r.season)+'</label>').join('')+'</div></fieldset>';
  const careerLabel=type==="player"?"Competition season totals from available snapshots":"Team season statistics from available snapshots";
  const history=statRows.map(r=>({season:r.season,...r.data,...(type==="team"?{matchesPlayed:teamStatValue(r.stats,"fixtures"),wins:teamStatValue(r.stats,"wins"),draws:teamStatValue(r.stats,"draws"),losses:teamStatValue(r.stats,"loses"),goalsFor:teamStatValue(r.stats,"goalsFor"),goalsAgainst:teamStatValue(r.stats,"goalsAgainst"),cleanSheets:teamStatValue(r.stats,"cleanSheet")}:{})}));
  const headers=type==="player"?[{label:"Season",key:"season"},{label:"Apps",key:"appearances"},{label:"Mins",key:"minutes"},{label:"Goals",key:"goals"},{label:"Assists",key:"assists"},{label:"xG",key:"expectedGoals"},{label:"xA",key:"expectedAssists"},{label:"Shots",key:"shots"},{label:"SoT",key:"shotsOnTarget"},{label:"Key passes",key:"keyPasses"},{label:"Tackles",key:"tackles"},{label:"Interceptions",key:"interceptions"},{label:"Y/R",render:r=>`${r.yellowCards??"—"}/${r.redCards??"—"}`}]:[{label:"Season",key:"season"},{label:"Played",key:"matchesPlayed"},{label:"Won",key:"wins"},{label:"Drawn",key:"draws"},{label:"Lost",key:"losses"},{label:"Goals for",key:"goalsFor"},{label:"Goals against",key:"goalsAgainst"},{label:"Clean sheets",key:"cleanSheets"},{label:"Shots",key:"shots"},{label:"xG",key:"xg"},{label:"Avg possession",key:"avgPossession"}];
  const rowsHtml=history.length?`<div class="table-scroll"><table class="data-table"><thead><tr>${headers.map(h=>`<th>${esc(h.label)}</th>`).join("")}</tr></thead><tbody>${history.map(r=>`<tr>${headers.map(h=>`<td>${esc(h.render?h.render(r):r[h.key]??"—")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`:`<div class="data-empty">No season statistics supplied.</div>`;
  panel.innerHTML=`<div class="panel-heading"><div><div class="eyebrow">${esc(item.name)} · ${esc(current.snapshot.provider||"Data source")}</div><h2>${esc(careerLabel)}</h2></div><span class="availability-pill is-ready"><i class="status-dot good"></i>${allTime?"All time":statRows.length===1?esc(statRows[0].season):`${statRows.length} seasons selected`}</span></div>${seasonControl}<div class="metric-grid">${metrics.map(m=>`<article class="metric-card"><span>${esc(m.label)}</span><strong>${esc(m.value)}</strong></article>`).join("")}</div><h3 class="subsection-title">Season-by-season</h3>${rowsHtml}<p class="source-note">Career totals only combine seasons present in this repository. Missing competitions and fields are not treated as zero.</p>`;
  const setProfileSeasons=(years,all=false)=>{const next=new URL(location.href);next.searchParams.delete("seasons");next.searchParams.delete("allTime");if(all){next.searchParams.set("allTime","1")}else if(years.length===1){next.searchParams.set("season",years[0])}else if(years.length>1){next.searchParams.delete("season");next.searchParams.set("seasons",years.join(","))}location.href=next.toString()};
  byId("profileAllTime")?.addEventListener("change",event=>setProfileSeasons(event.target.checked?availableRows.map(r=>r.year):[current.year],event.target.checked));
  panel.querySelectorAll("[data-profile-season]").forEach(input=>input.addEventListener("change",()=>{const chosen=[...panel.querySelectorAll("[data-profile-season]:checked")].map(box=>box.dataset.profileSeason);setProfileSeasons(chosen.length?chosen:[input.dataset.profileSeason])}));
}

async function initMatchPage(){
  const hero=byId("matchHero"),panel=byId("matchPanel");if(!hero||!panel)return;
  const params=new URLSearchParams(location.search),id=params.get("id"),competitionId=params.get("competition"),season=params.get("season"),item=COMPETITIONS.find(c=>c.id===competitionId);
  if(!id||!item){panel.innerHTML=`<div class="data-empty">Choose a fixture from a competition page.</div>`;return}
  byId("matchBack").href=`./competition.html?id=${encodeURIComponent(item.id)}&season=${encodeURIComponent(season||"")}`;
  let snapshot=null;try{snapshot=await fetchSnapshot(`./data/competitions/${encodeURIComponent(item.id)}-${encodeURIComponent(season)}.json`)}catch{}
  const fixture=snapshot?.fixtures?.find(f=>String(f.id)===String(id));
  if(!fixture){hero.innerHTML=`<div class="eyebrow">${esc(item.name)} · ${esc(season||"")}</div><h1 class="title">Match details <span>unavailable.</span></h1>`;panel.innerHTML=`<div class="unavailable"><h2>No published match data</h2><p>${esc(DATA_MESSAGE)}</p><a class="text-link" href="./health.html">Check data status →</a></div>`;return}
  const score=fixture.goals?.home==null||fixture.goals?.away==null?"vs":`${fixture.goals.home} – ${fixture.goals.away}`;
  hero.innerHTML=`<div class="competition-kicker"><a class="text-link" href="./competition.html?id=${encodeURIComponent(item.id)}&season=${encodeURIComponent(season)}">${esc(item.name)}</a><span>·</span><span>${esc(fixture.round||"")}</span></div><div class="match-scoreline"><div><img src="${esc(fixture.home?.logo||"")}" alt="" loading="lazy"><h1>${esc(fixture.home?.name||"Home")}</h1></div><strong>${esc(score)}</strong><div><img src="${esc(fixture.away?.logo||"")}" alt="" loading="lazy"><h1>${esc(fixture.away?.name||"Away")}</h1></div></div><p class="subtitle">${esc(formatDate(fixture.date))} · ${esc(fixture.venue||"Venue unavailable")} · ${esc(fixture.statusLong||fixture.status||"Status unavailable")}</p>`;
  let stats=snapshot.fixtureStats?.[String(id)]||[],events=snapshot.events?.[String(id)]||[],lineups=snapshot.lineups?.[String(id)]||[];
  let sourceLabel=snapshot.provider||"Open data";
  if(fixture.statsbombMatchId){
    try{
      const base=`https://raw.githubusercontent.com/hudl/open-data/master/data`;
      const [eventResponse,lineupResponse]=await Promise.all([fetch(`${base}/events/${fixture.statsbombMatchId}.json`),fetch(`${base}/lineups/${fixture.statsbombMatchId}.json`)]);
      const sbEvents=eventResponse.ok?await eventResponse.json():[];
      const sbLineups=lineupResponse.ok?await lineupResponse.json():[];
      const teamNames=[fixture.home?.name,fixture.away?.name];
      const aggregate=Object.fromEntries(teamNames.map(name=>[name,{team:name,teamId:name===fixture.home?.name?fixture.home?.id:fixture.away?.id,statistics:{"Shots":0,"Shots on target":0,"Goals":0,"xG":0,"Yellow cards":0,"Red cards":0,"Corners":0}}]));
      for(const ev of sbEvents){const team=ev.team?.name,entry=aggregate[team];if(!entry)continue;const type=ev.type?.name||"";if(type==="Shot"){entry.statistics["Shots"]++;if(["Goal","Saved","Saved To Post"].includes(ev.shot?.outcome?.name))entry.statistics["Shots on target"]++;if(ev.shot?.outcome?.name==="Goal")entry.statistics["Goals"]++;entry.statistics.xG+=Number(ev.shot?.statsbomb_xg||0)}if(type==="Foul Committed"){const card=ev.foul_committed?.card?.name||"";if(card.includes("Yellow"))entry.statistics["Yellow cards"]++;if(card.includes("Red"))entry.statistics["Red cards"]++}if(type==="Corner Awarded")entry.statistics.Corners++}
      stats=Object.values(aggregate).map(row=>({...row,statistics:{...row.statistics,"xG":row.statistics.xG.toFixed(2)}}));
      events=sbEvents.filter(ev=>["Shot","Foul Committed","Substitution","Own Goal Against"].includes(ev.type?.name)).map(ev=>({time:{elapsed:ev.minute},team:ev.team?.name,type:ev.type?.name,detail:ev.type?.name==="Shot"?(ev.shot?.outcome?.name||"Shot"):ev.foul_committed?.card?.name||ev.substitution?.replacement?.name||"",player:ev.player?.name}));
      lineups=sbLineups.map(team=>({team:team.team_name,formation:"StatsBomb lineup",coach:"",startXI:(team.lineup||[]).filter(p=>(p.positions||[]).some(pos=>pos.position!=="Substitute")).map(p=>({name:p.player_name})),substitutes:(team.lineup||[]).filter(p=>(p.positions||[]).some(pos=>pos.position==="Substitute")).map(p=>({name:p.player_name}))}));
      sourceLabel="StatsBomb Open Data · event data";
    }catch{sourceLabel="StatsBomb Open Data · event file unavailable"}
  }
  const statTypes=[...new Set(stats.flatMap(team=>Object.keys(team.statistics||{})))];
  const statTable=statTypes.length?`<div class="table-scroll"><table class="data-table"><thead><tr><th>${esc(fixture.home?.name||"Home")}</th><th>Match statistic</th><th>${esc(fixture.away?.name||"Away")}</th></tr></thead><tbody>${statTypes.map(type=>`<tr><td>${esc(stats.find(t=>String(t.teamId)===String(fixture.home?.id))?.statistics?.[type]??"—")}</td><th>${esc(type)}</th><td>${esc(stats.find(t=>String(t.teamId)===String(fixture.away?.id))?.statistics?.[type]??"—")}</td></tr>`).join("")}</tbody></table></div>`:`<div class="data-empty">Match statistics unavailable for this fixture.</div>`;
  const eventRows=events.map(e=>({...e,minute:`${e.time?.elapsed??""}${e.time?.extra?`+${e.time.extra}`:""}`,description:[e.type,e.detail,e.player,e.assist?`Assist: ${e.assist}`:""].filter(Boolean).join(" · ")}));
  const eventTable=eventRows.length?`<div class="table-scroll"><table class="data-table"><thead><tr><th>Minute</th><th>Team</th><th>Event</th></tr></thead><tbody>${eventRows.map(e=>`<tr><td>${esc(e.minute||"—")}</td><td>${esc(e.team||"—")}</td><td>${esc(e.description)}</td></tr>`).join("")}</tbody></table></div>`:`<div class="data-empty">Match events unavailable.</div>`;
  const lineupHtml=lineups.length?`<div class="entity-grid">${lineups.map(team=>`<article class="record-card"><span>${esc(team.formation||"Formation unavailable")} · ${esc(team.coach||"Coach unavailable")}</span><strong>${esc(team.team||"Team")}</strong><small>Starting XI: ${esc((team.startXI||[]).map(p=>p.name).join(", ")||"Unavailable")}</small><small>Substitutes: ${esc((team.substitutes||[]).map(p=>p.name).join(", ")||"Unavailable")}</small></article>`).join("")}</div>`:`<div class="data-empty">Lineups unavailable for this fixture.</div>`;
  panel.innerHTML=`<section class="data-subpanel"><h2>Match statistics</h2>${statTable}</section><section class="data-subpanel"><h2>Events</h2>${eventTable}</section><section class="data-subpanel"><h2>Lineups</h2>${lineupHtml}</section><p class="source-note">${esc(sourceLabel)} · ${fixture.statsbombMatchId?'<a href="https://github.com/hudl/open-data" target="_blank" rel="noopener noreferrer">StatsBomb Open Data source</a>':esc(snapshot.generatedAt||"static snapshot")}. Values appear only when supplied by the source.</p>`;
}

async function initHealthPage(){
  const root=byId("healthDashboard");if(!root)return;
  let coverage=null;try{const r=await fetch("./data/coverage.json?v="+Date.now());if(r.ok)coverage=await r.json()}catch{}
  if(!coverage){root.innerHTML=`<div class="panel"><div class="unavailable"><h2>Coverage file unavailable</h2><p>Could not read data/coverage.json.</p></div></div>`;return}
  const entries=Object.entries(coverage.competitions||{});
  const counts=[ ["Fixtures & results",entries.filter(([,r])=>r.fixtures?.available).length], ["Tables",entries.filter(([,r])=>r.standings?.available).length], ["Team lists",entries.filter(([,r])=>r.teams?.available).length], ["Player season totals",entries.filter(([,r])=>r.players?.available||r.topScorers?.available).length] ];
  const cell=(state)=>state?.available?`<span class="coverage-ready">Available</span><small>${esc(state.rows??"")} rows</small>`:`<span class="coverage-missing">${esc(state?.note||"Not covered")}</span>`;
  const rows=COMPETITIONS.map(item=>{const row=coverage.competitions?.[item.id]||{};return `<tr><td><a class="data-link" href="./competition.html?id=${encodeURIComponent(item.id)}">${esc(item.name)}</a><small>${esc((row.seasons||[]).join(", ")||"No published season")}</small></td><td>${cell(row.fixtures)}</td><td>${cell(row.standings)}</td><td>${cell(row.teams)}</td><td>${cell(row.players||row.topScorers)}</td><td>${cell(row.cornerflick||row.openmatchday||row.statsbomb)}</td></tr>`}).join("");
  const sources=(coverage.sources||[]).map(source=>`<li><a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(source.name)}</a> · ${esc(source.license)}</li>`).join("");
  root.innerHTML=`<section class="status-grid"><article class="status-card"><span class="status-label"><i class="status-dot good"></i>Static open data</span><h2>${esc(coverage.provider||"Open datasets")}</h2><p>${esc(coverage.message||"Coverage varies by source and competition.")}</p><p class="source-note">Last refresh: ${esc(coverage.generatedAt||"not yet run")}</p></article><article class="status-card"><span class="status-label"><i class="status-dot good"></i>Competition directory</span><h2>${COMPETITIONS.length} competitions</h2><p>All directory pages work; published data depends on the open files available for each season.</p></article><article class="status-card"><span class="status-label"><i class="status-dot pending"></i>Coverage snapshot</span><h2>By data section</h2><div class="mini-counts">${counts.map(([label,count])=>`<span>${esc(label)} <strong>${count}/${COMPETITIONS.length}</strong></span>`).join("")}</div></article></section><section class="panel source-panel"><div class="eyebrow">Sources & limits</div><h2>Public datasets, no key required</h2><p>Open-matchday supplies 2026/27 fixtures, results and selected match statistics for the five major leagues, UEFA Champions/Europa/Conference Leagues and English FA/EFL Cups; use is non-commercial with attribution. FPL Core Insights supplies the current Premier League squad, player season totals and player match statistics as public CSV snapshots; credit the dataset when reusing it. Cornerflick supplies Ekstraklasa reports, events, lineups and statistics under CC BY 4.0. StatsBomb Open Data supplies selected historical match event and lineup files. These are static feeds, not live, and player season totals vary by source. The Polish cups remain listed but have no current-season feed in these sources.</p><ul>${sources}</ul><p>Match pages attribute data to its provider. See each source for its data terms and attribution requirements.</p></section><section class="panel coverage-panel"><div class="panel-heading"><div><div class="eyebrow">Per competition · per season</div><h2>Published data coverage</h2></div><span class="source-note">Unavailable means no matching open file</span></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Competition</th><th>Fixtures & results</th><th>Table</th><th>Teams</th><th>Players</th><th>Detailed match data</th></tr></thead><tbody>${rows}</tbody></table></div></section>`;
}

function renderGlobalRows(view,rows){
  if(view==="teams")return rows.length?`<div class="entity-grid">${rows.map(r=>`<a class="entity-card" href="./entity.html?type=team&id=${encodeURIComponent(r.id)}&competition=${encodeURIComponent(r.competitionId)}&season=${encodeURIComponent(r.season)}">${r.logo?`<img src="${esc(r.logo)}" alt="" loading="lazy">`:""}<strong>${esc(r.name)}</strong><span>${esc(r.competition)} · ${esc(r.country||"")}</span></a>`).join("")}</div>`:`<div class="data-empty">No team rows are available.</div>`;
  if(view==="players")return rows.length?`<div class="entity-grid">${rows.map(r=>`<a class="entity-card" href="./entity.html?type=player&id=${encodeURIComponent(r.id)}&competition=${encodeURIComponent(r.competitionId)}&season=${encodeURIComponent(r.season)}">${r.photo?`<img src="${esc(r.photo)}" alt="" loading="lazy">`:""}<strong>${esc(r.name)}</strong><span>${esc(r.team||"")} · ${esc(r.competition)}</span><span>${esc(r.position||"")} · ${esc(r.goals??"—")} goals · ${esc(r.assists??"—")} assists</span></a>`).join("")}</div>`:`<div class="data-empty">No player rows are available.</div>`;
  if(view==="calendar")return rows.length?`<div class="table-scroll"><table class="data-table"><thead><tr><th>Date</th><th>Competition</th><th>Home</th><th>Score</th><th>Away</th><th>Status</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(formatDate(r.date))}</td><td><a class="data-link" href="./competition.html?id=${encodeURIComponent(r.competitionId)}">${esc(r.competition)}</a></td><td>${esc(r.home?.name||"—")}</td><td><a class="data-link" href="./match.html?id=${encodeURIComponent(r.id)}&competition=${encodeURIComponent(r.competitionId)}&season=${encodeURIComponent(r.season)}"><strong>${esc(r.goals?.home==null||r.goals?.away==null?"—":`${r.goals.home} – ${r.goals.away}`)}</strong></a></td><td>${esc(r.away?.name||"—")}</td><td>${esc(r.statusLong||r.status||"—")}</td></tr>`).join("")}</tbody></table></div>`:`<div class="data-empty">No fixture rows are available.</div>`;
  return rows.length?`<div class="entity-grid">${rows.map(r=>`<article class="record-card"><span>${esc(r.competition)} · ${esc(r.season)}</span><strong>${esc(r.label)}</strong><small>${esc(r.value)}</small></article>`).join("")}</div>`:`<div class="data-empty">No record rows are available.</div>`;
}

function recordRows(snapshot,item,season){
  const finished=(snapshot.fixtures||[]).filter(f=>["FT","AET","PEN"].includes(f.status)&&Number.isFinite(f.goals?.home)&&Number.isFinite(f.goals?.away));
  const maxGoal=finished.reduce((best,f)=>(f.goals.home+f.goals.away)>(best?.goals.home+best?.goals.away||-1)?f:best,null);
  const biggest=finished.reduce((best,f)=>Math.abs(f.goals.home-f.goals.away)>Math.abs(best?.goals.home-best?.goals.away||0)?f:best,null);
  const top=snapshot.topScorers?.[0];
  return [["Highest scoring match",maxGoal?`${maxGoal.home.name} ${maxGoal.goals.home}-${maxGoal.goals.away} ${maxGoal.away.name}`:null],["Largest score margin",biggest?`${biggest.home.name} ${biggest.goals.home}-${biggest.goals.away} ${biggest.away.name}`:null],["Top scorer",top?`${top.name} · ${top.goals??"—"} goals`:null]].filter(row=>row[1]).map(([label,value])=>({competition:item.name,competitionId:item.id,season,label,value}))
}

function formatDate(value){if(!value)return"—";const d=new Date(value);return Number.isNaN(d.valueOf())?value:new Intl.DateTimeFormat(undefined,{dateStyle:"medium",timeStyle:"short"}).format(d)}
function renderH2H(fixtures,firstId,secondId,teams){
  if(!firstId||!secondId||firstId===secondId)return `<div class="data-empty">Choose two different teams.</div>`;
  const meetings=[...fixtures].sort((a,b)=>String(b.date||"").localeCompare(String(a.date||"")));
  const completed=meetings.filter(f=>["FT","AET","PEN"].includes(f.status)&&f.goals?.home!=null&&f.goals?.away!=null);
  let firstWins=0,secondWins=0,draws=0,biggest=null;
  for(const f of completed){const firstHome=String(f.home?.id)===String(firstId),a=firstHome?Number(f.goals.home):Number(f.goals.away),b=firstHome?Number(f.goals.away):Number(f.goals.home);if(a>b)firstWins++;else if(a<b)secondWins++;else draws++;if(!biggest||Math.abs(a-b)>Math.abs(biggest.margin))biggest={fixture:f,margin:a-b}}
  const first=teams.find(t=>String(t.id)===String(firstId)),second=teams.find(t=>String(t.id)===String(secondId));
  const rows=meetings.map(f=>`<tr><td>${esc(formatDate(f.date))}</td><td>${esc(f.round||"—")}</td><td>${esc(f.home?.name||"—")}</td><td><strong>${esc(f.goals?.home==null||f.goals?.away==null?"—":`${f.goals.home} – ${f.goals.away}`)}</strong></td><td>${esc(f.away?.name||"—")}</td><td>${esc(f.statusLong||f.status||"—")}</td></tr>`).join("");
  const table=rows?`<div class="table-scroll"><table class="data-table"><thead><tr><th>Date</th><th>Round</th><th>Home</th><th>Score</th><th>Away</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table></div>`:`<div class="data-empty">No meetings between these clubs appear in this season snapshot.</div>`;
  return `<div class="metric-grid"><article class="metric-card"><span>${esc(first?.name||"Team A")} wins</span><strong>${firstWins}</strong></article><article class="metric-card"><span>Draws</span><strong>${draws}</strong></article><article class="metric-card"><span>${esc(second?.name||"Team B")} wins</span><strong>${secondWins}</strong></article></div><h3 class="subsection-title">Meetings in this season snapshot</h3>${table}${biggest?`<p class="source-note">Biggest margin in completed meetings: ${esc(biggest.fixture.home.name)} ${esc(biggest.fixture.goals.home)}–${esc(biggest.fixture.goals.away)} ${esc(biggest.fixture.away.name)}.</p>`:""}`
}

async function boot(){
  try {
    const response=await fetch("./data/competitions.json?v="+Date.now());
    if(!response.ok) throw new Error("Competition catalogue unavailable");
    COMPETITIONS=await response.json();
  } catch (error) {
    const root=byId("competitionGroups");
    if(root) root.innerHTML=`<div class="unavailable"><h2>Could not load the competition directory</h2><p>${esc(error.message)}. Open the site through GitHub Pages or a local web server.</p></div>`;
  }
  initDirectory();
  initCompetitionPage();
  initEntityPage();
  initMatchPage();
  initHealthPage();
}
boot();
