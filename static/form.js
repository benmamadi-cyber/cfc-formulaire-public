'use strict';
(function () {
  const VILLES = JSON.parse(document.getElementById('villes-data').textContent || '{}');

  // Remplit un <datalist> de villes selon la région choisie.
  function lierRegionVilles(selRegion, datalistId, inputVille) {
    const dl = document.getElementById(datalistId);
    const input = document.getElementById(inputVille);
    function maj() {
      const villes = VILLES[selRegion.value] || [];
      dl.innerHTML = villes.map(v => `<option value="${v}">`).join('');
      if (input && !villes.includes(input.value)) input.value = input.value; // conserve saisie libre
    }
    selRegion.addEventListener('change', maj);
    maj();
  }
  lierRegionVilles(document.getElementById('region-res'), 'villes-res', 'ville-res');
  lierRegionVilles(document.getElementById('region-projet'), 'villes-projet', 'ville-projet');

  // Affiche/masque les blocs conditionnels.
  const cPret = document.getElementById('c-pret');
  const cEpargne = document.getElementById('c-epargne');
  const blocPret = document.getElementById('bloc-pret');
  const blocEpargne = document.getElementById('bloc-epargne');
  const regionProjet = document.getElementById('region-projet');
  function majCentres() {
    blocPret.hidden = !cPret.checked;
    blocEpargne.hidden = !cEpargne.checked;
    regionProjet.required = cPret.checked;
  }
  cPret.addEventListener('change', majCentres);
  cEpargne.addEventListener('change', majCentres);
  majCentres();

  // Bloc RDV.
  const rdvChk = document.getElementById('rdv-chk');
  const blocRdv = document.getElementById('bloc-rdv');
  rdvChk.addEventListener('change', () => { blocRdv.hidden = !rdvChk.checked; });

  // Normalise les montants (retire espaces) avant envoi ; simple confort.
  const form = document.getElementById('form-prospect');
  const erreur = document.getElementById('form-erreur');
  const btn = document.getElementById('btn-envoyer');

  function afficherErreur(msg) {
    erreur.textContent = msg;
    erreur.hidden = false;
    erreur.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    erreur.hidden = true;

    // Validations côté client (miroir serveur, UX rapide).
    const tel = (form.telephone.value || '').replace(/\s/g, '');
    if (!/^6\d{8}$/.test(tel)) return afficherErreur('Numéro de téléphone invalide (6 suivi de 8 chiffres).');
    if (!cPret.checked && !cEpargne.checked) return afficherErreur("Sélectionnez au moins un centre d'intérêt.");
    if (cPret.checked && !regionProjet.value) return afficherErreur('Indiquez la région du lieu de votre projet.');

    const data = new FormData(form);
    btn.disabled = true; btn.textContent = 'Envoi en cours…';
    try {
      const resp = await fetch('/api/soumission', { method: 'POST', body: data });
      const json = await resp.json();
      if (!resp.ok || !json.ok) {
        afficherErreur(json.msg || 'Une erreur est survenue. Merci de réessayer.');
        btn.disabled = false; btn.textContent = 'Envoyer ma demande';
        return;
      }
      // Succès : bascule sur l'écran de remerciement.
      form.hidden = true;
      document.getElementById('ref-valeur').textContent = json.reference;
      document.getElementById('ecran-merci').hidden = false;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      afficherErreur('Connexion impossible. Vérifiez votre réseau et réessayez.');
      btn.disabled = false; btn.textContent = 'Envoyer ma demande';
    }
  });
})();
