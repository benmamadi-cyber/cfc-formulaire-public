/* Décorations saisonnières du logo, selon la date du jour.
 * Règles :
 *  - 25 nov → 1er déc : ruban rouge (journée mondiale de lutte contre le sida, 1er décembre)
 *  - semaine du 1er lundi d'octobre : maison (journée mondiale de l'habitat)
 *  - tout décembre : chapeau de père Noël + guirlande lumineuse
 * Aperçu forcé possible via ?deco=vih | habitat | noel (cumulables : ?deco=noel,vih)
 */
(function () {
  var logo = document.querySelector('.cfc-logo');
  if (!logo) return;

  var SVG_RUBAN =
    '<svg viewBox="0 0 64 64" aria-label="Ruban rouge — lutte contre le VIH/sida" role="img">' +
    '<rect x="26" y="10" width="12" height="50" rx="5" fill="#e2001a" transform="rotate(18 32 35)"/>' +
    '<rect x="26" y="10" width="12" height="50" rx="5" fill="#c00016" transform="rotate(-18 32 35)"/>' +
    '<ellipse cx="32" cy="16" rx="9" ry="11" fill="none" stroke="#e2001a" stroke-width="11"/>' +
    '</svg>';

  var SVG_MAISON =
    '<svg viewBox="0 0 64 64" aria-label="Journée mondiale de l’habitat" role="img">' +
    '<path d="M32 6 4 30h9v26h15V40h8v16h15V30h9z" fill="#e8792b"/>' +
    '<path d="M32 6 4 30h9l19-16 19 16h9z" fill="#8a1538"/>' +
    '</svg>';

  var SVG_CHAPEAU =
    '<svg viewBox="0 0 84 58" aria-label="Chapeau de père Noël" role="img">' +
    '<path d="M14 42 C18 16 44 4 62 12 c7 3 10 9 8 15 l-4 12 Z" fill="#d6001c"/>' +
    '<path d="M14 42 C20 24 36 12 52 12 c-14 2 -26 14 -30 30 Z" fill="#ff2a3c" opacity=".55"/>' +
    '<circle cx="70" cy="13" r="8" fill="#fff"/>' +
    '<rect x="8" y="38" width="64" height="13" rx="6.5" fill="#fff"/>' +
    '</svg>';

  function ajouterBadge(svg) {
    var s = document.createElement('span');
    s.className = 'logo-badge';
    s.innerHTML = svg;
    logo.appendChild(s);
  }

  function ajouterChapeau() {
    var s = document.createElement('span');
    s.className = 'logo-chapeau';
    s.innerHTML = SVG_CHAPEAU;
    logo.appendChild(s);
  }

  function ajouterLumieres() {
    var s = document.createElement('span');
    s.className = 'logo-lumieres';
    for (var i = 0; i < 12; i++) s.appendChild(document.createElement('i'));
    logo.appendChild(s);
  }

  function premierLundiOctobre(annee) {
    var d = new Date(annee, 9, 1);
    return new Date(annee, 9, 1 + ((8 - d.getDay()) % 7));
  }

  var force = (new URLSearchParams(location.search).get('deco') || '')
    .toLowerCase().split(',').filter(Boolean);
  var auj = new Date();
  var mois = auj.getMonth(); // 0 = janvier
  var jourMs = 24 * 3600 * 1000;

  // Ruban rouge : du 25 novembre au 1er décembre
  var vih = (mois === 10 && auj.getDate() >= 25) ||
            (mois === 11 && auj.getDate() === 1);

  // Maison : semaine (lun→dim) du premier lundi d'octobre
  var lundi = premierLundiOctobre(auj.getFullYear());
  var habitat = mois === 9 && auj >= lundi && auj < new Date(lundi.getTime() + 7 * jourMs);

  // Décembre : père Noël + guirlande
  var noel = mois === 11;

  if (force.length) {
    vih = force.indexOf('vih') !== -1;
    habitat = force.indexOf('habitat') !== -1;
    noel = force.indexOf('noel') !== -1;
  }

  if (vih) ajouterBadge(SVG_RUBAN);
  else if (habitat) ajouterBadge(SVG_MAISON);
  if (noel) { ajouterChapeau(); ajouterLumieres(); }
})();
