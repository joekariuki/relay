"""DuniaWallet service policies in English and French."""

from __future__ import annotations

from .models import Policy


def _build_policies() -> dict[str, Policy]:
    """Create policy documents for all supported topics."""
    policies = [
        Policy(
            topic="transaction_limits",
            title_en="Transaction Limits",
            content_en=(
                "DuniaWallet transaction limits depend on your KYC verification tier. "
                "Basic tier (phone verification only): 50,000 FCFA daily send limit, "
                "200,000 FCFA monthly limit. Standard tier (government ID verified): "
                "500,000 FCFA daily send limit, 2,000,000 FCFA monthly limit. "
                "Premium tier (full KYC with proof of address): 2,000,000 FCFA daily "
                "send limit, 10,000,000 FCFA monthly limit. To upgrade your tier, "
                "visit any DuniaWallet agent with your government-issued ID."
            ),
            title_fr="Limites de transaction",
            content_fr=(
                "Les limites de transaction DuniaWallet dependent de votre niveau de "
                "verification KYC. Niveau basique (verification telephone uniquement) : "
                "limite d'envoi journaliere de 50 000 FCFA, limite mensuelle de "
                "200 000 FCFA. Niveau standard (piece d'identite verifiee) : limite "
                "journaliere de 500 000 FCFA, limite mensuelle de 2 000 000 FCFA. "
                "Niveau premium (KYC complet avec justificatif de domicile) : limite "
                "journaliere de 2 000 000 FCFA, limite mensuelle de 10 000 000 FCFA. "
                "Pour ameliorer votre niveau, visitez un agent DuniaWallet avec votre "
                "piece d'identite officielle."
            ),
        ),
        Policy(
            topic="fees",
            title_en="Fee Structure",
            content_en=(
                "DuniaWallet fees vary by transfer type and amount. Domestic transfers: "
                "1% of the amount (minimum 100 FCFA, maximum 5,000 FCFA). International "
                "transfers within WAEMU zone (Senegal, Mali, Cote d'Ivoire, Burkina Faso): "
                "1.5% of the amount (minimum 150 FCFA). Cash-in deposits are free. "
                "Cash-out withdrawals: 1% of the amount (minimum 100 FCFA). Bill payments: "
                "flat fee of 100-500 FCFA depending on the biller. Airtime purchases "
                "have no fee. Fees are deducted from the sender's balance at the time "
                "of the transaction."
            ),
            title_fr="Grille tarifaire",
            content_fr=(
                "Les frais DuniaWallet varient selon le type et le montant du transfert. "
                "Transferts nationaux : 1% du montant (minimum 100 FCFA, maximum "
                "5 000 FCFA). Transferts internationaux dans la zone UEMOA (Senegal, "
                "Mali, Cote d'Ivoire, Burkina Faso) : 1,5% du montant (minimum "
                "150 FCFA). Les depots sont gratuits. Retraits : 1% du montant "
                "(minimum 100 FCFA). Paiements de factures : frais fixes de 100 a "
                "500 FCFA selon le facturier. Les achats de credit telephonique sont "
                "sans frais. Les frais sont preleves sur le solde de l'expediteur au "
                "moment de la transaction."
            ),
        ),
        Policy(
            topic="kyc_verification",
            title_en="KYC Verification",
            content_en=(
                "DuniaWallet requires Know Your Customer (KYC) verification to comply "
                "with financial regulations. Basic level requires only phone number "
                "verification via SMS. Standard level requires a valid government-issued "
                "ID (national ID card, passport, or driver's license) verified at any "
                "DuniaWallet agent. Premium level requires full KYC including proof of "
                "address (utility bill or bank statement less than 3 months old) and "
                "in-person verification. Verification typically takes 24-48 hours for "
                "Standard and 3-5 business days for Premium. You can check your "
                "verification status in the app settings."
            ),
            title_fr="Verification KYC",
            content_fr=(
                "DuniaWallet exige une verification KYC (Know Your Customer) pour "
                "respecter les reglementations financieres. Le niveau basique ne "
                "necessite que la verification du numero de telephone par SMS. Le "
                "niveau standard necessite une piece d'identite officielle (carte "
                "nationale, passeport ou permis de conduire) verifiee chez un agent "
                "DuniaWallet. Le niveau premium necessite un KYC complet incluant un "
                "justificatif de domicile (facture ou releve bancaire de moins de "
                "3 mois) et une verification en personne. La verification prend "
                "generalement 24 a 48 heures pour le niveau standard et 3 a 5 jours "
                "ouvrables pour le niveau premium."
            ),
        ),
        Policy(
            topic="dispute_resolution",
            title_en="Dispute Resolution",
            content_en=(
                "If you believe a transaction was made in error or you were charged "
                "incorrectly, you can file a dispute within 30 days of the transaction. "
                "To file a dispute: contact our support team with the transaction ID "
                "and a description of the issue. Our team will investigate within "
                "5 business days. If the dispute is resolved in your favor, the amount "
                "will be credited back to your account. For urgent disputes involving "
                "unauthorized transactions, please call our emergency line immediately. "
                "DuniaWallet is not responsible for transfers sent to the wrong recipient "
                "if the sender confirmed the transaction details."
            ),
            title_fr="Resolution des litiges",
            content_fr=(
                "Si vous pensez qu'une transaction a ete effectuee par erreur ou que "
                "vous avez ete facture incorrectement, vous pouvez deposer une "
                "reclamation dans les 30 jours suivant la transaction. Pour deposer "
                "une reclamation : contactez notre equipe de support avec l'identifiant "
                "de la transaction et une description du probleme. Notre equipe "
                "enquete sous 5 jours ouvrables. Si la reclamation est resolue en "
                "votre faveur, le montant sera recredite sur votre compte. Pour les "
                "litiges urgents impliquant des transactions non autorisees, veuillez "
                "appeler notre ligne d'urgence immediatement."
            ),
        ),
        Policy(
            topic="account_security",
            title_en="Account Security",
            content_en=(
                "Protect your DuniaWallet account with these security measures: "
                "Never share your PIN or password with anyone, including DuniaWallet "
                "agents or staff. Enable two-factor authentication in your app settings. "
                "DuniaWallet will never ask for your full PIN via phone call, SMS, or "
                "email. If you suspect unauthorized access, lock your account immediately "
                "through the app or by calling our support line. Report any suspicious "
                "activity within 24 hours to minimize liability. Change your PIN "
                "regularly and avoid using easily guessable numbers like your birth date."
            ),
            title_fr="Securite du compte",
            content_fr=(
                "Protegez votre compte DuniaWallet avec ces mesures de securite : "
                "Ne partagez jamais votre code PIN ou mot de passe avec quiconque, y "
                "compris les agents ou employes DuniaWallet. Activez l'authentification "
                "a deux facteurs dans les parametres de l'application. DuniaWallet ne "
                "vous demandera jamais votre code PIN complet par telephone, SMS ou "
                "email. Si vous suspectez un acces non autorise, verrouillez votre "
                "compte immediatement via l'application ou en appelant notre service "
                "client. Signalez toute activite suspecte dans les 24 heures."
            ),
        ),
        Policy(
            topic="send_money_international",
            title_en="International Transfers",
            content_en=(
                "DuniaWallet supports international transfers within the WAEMU zone: "
                "Senegal, Mali, Cote d'Ivoire, Burkina Faso, Togo, Benin, Niger, and "
                "Guinea-Bissau. All transfers are in CFA Francs (XOF). Transfer fees "
                "for international transfers are 1.5% of the amount (minimum 150 FCFA). "
                "Transfers are typically completed within minutes for Standard and "
                "Premium tier users. Basic tier users may experience delays of up to "
                "24 hours. The recipient must have a DuniaWallet account or can collect "
                "cash at any DuniaWallet agent in the destination country."
            ),
            title_fr="Transferts internationaux",
            content_fr=(
                "DuniaWallet prend en charge les transferts internationaux dans la zone "
                "UEMOA : Senegal, Mali, Cote d'Ivoire, Burkina Faso, Togo, Benin, "
                "Niger et Guinee-Bissau. Tous les transferts sont en Francs CFA (XOF). "
                "Les frais pour les transferts internationaux sont de 1,5% du montant "
                "(minimum 150 FCFA). Les transferts sont generalement completes en "
                "quelques minutes pour les utilisateurs des niveaux Standard et Premium. "
                "Les utilisateurs du niveau basique peuvent subir des delais allant "
                "jusqu'a 24 heures."
            ),
        ),
        Policy(
            topic="cash_in_cash_out",
            title_en="Cash-In and Cash-Out",
            content_en=(
                "Cash-in (depositing money) is free at all DuniaWallet agents. Simply "
                "visit any agent, provide your phone number, and hand over the cash. "
                "The agent will confirm the deposit and the funds will appear in your "
                "account immediately. Cash-out (withdrawing money) costs 1% of the "
                "amount (minimum 100 FCFA). Visit any agent, request a withdrawal, "
                "confirm with your PIN, and receive your cash. Daily cash-out limits "
                "apply based on your KYC tier. Agents are available in major cities "
                "and many smaller towns across our operating countries."
            ),
            title_fr="Depot et retrait",
            content_fr=(
                "Les depots d'argent (cash-in) sont gratuits chez tous les agents "
                "DuniaWallet. Visitez simplement un agent, fournissez votre numero "
                "de telephone et remettez l'argent. L'agent confirmera le depot et les "
                "fonds apparaitront immediatement sur votre compte. Les retraits "
                "(cash-out) coutent 1% du montant (minimum 100 FCFA). Visitez un "
                "agent, demandez un retrait, confirmez avec votre code PIN et recevez "
                "votre argent. Les limites de retrait journalieres s'appliquent selon "
                "votre niveau KYC."
            ),
        ),
        Policy(
            topic="agent_locations",
            title_en="Finding Agents",
            content_en=(
                "DuniaWallet agents are available across Senegal, Mali, Cote d'Ivoire, "
                "and Burkina Faso. You can find the nearest agent using the 'Find Agent' "
                "feature in the app, which shows agents on a map with their operating "
                "hours and available services. Most agents operate from 8:00 AM to "
                "8:00 PM, Monday through Saturday. Some agents in major markets are "
                "also open on Sundays. Each agent can provide cash-in, cash-out, and "
                "new account registration services. For large transactions (over "
                "500,000 FCFA), we recommend calling the agent in advance to ensure "
                "they have sufficient cash available."
            ),
            title_fr="Trouver un agent",
            content_fr=(
                "Les agents DuniaWallet sont disponibles au Senegal, Mali, Cote "
                "d'Ivoire et Burkina Faso. Vous pouvez trouver l'agent le plus proche "
                "en utilisant la fonction 'Trouver un agent' dans l'application, qui "
                "affiche les agents sur une carte avec leurs horaires et services "
                "disponibles. La plupart des agents operent de 8h a 20h, du lundi au "
                "samedi. Certains agents dans les grands marches sont egalement ouverts "
                "le dimanche. Chaque agent peut fournir des services de depot, retrait "
                "et creation de compte."
            ),
        ),
        Policy(
            topic="account_closure",
            title_en="Account Closure",
            content_en=(
                "To close your DuniaWallet account, you must first withdraw or transfer "
                "all remaining funds. Then contact our support team to request account "
                "closure. The account will be deactivated within 48 hours. You can "
                "reopen a closed account within 90 days by contacting support. After "
                "90 days, account data is archived and you would need to create a new "
                "account. Any pending transactions at the time of closure will be "
                "cancelled and refunded. Please ensure you have no pending disputes "
                "before requesting closure."
            ),
            title_fr="Fermeture de compte",
            content_fr=(
                "Pour fermer votre compte DuniaWallet, vous devez d'abord retirer ou "
                "transferer tous les fonds restants. Contactez ensuite notre equipe de "
                "support pour demander la fermeture du compte. Le compte sera desactive "
                "sous 48 heures. Vous pouvez reouvrir un compte ferme dans les 90 jours "
                "en contactant le support. Apres 90 jours, les donnees du compte sont "
                "archivees et vous devrez creer un nouveau compte. Toute transaction en "
                "attente au moment de la fermeture sera annulee et remboursee."
            ),
        ),
        Policy(
            topic="privacy_policy",
            title_en="Privacy Policy",
            content_en=(
                "DuniaWallet collects and processes personal data in accordance with "
                "applicable data protection laws. We collect your name, phone number, "
                "ID information (for KYC), and transaction history. This data is used "
                "solely for providing our services, fraud prevention, and regulatory "
                "compliance. We do not sell your personal data to third parties. You "
                "have the right to access, correct, or delete your personal data by "
                "contacting our support team. Transaction data is retained for 5 years "
                "as required by financial regulations."
            ),
            title_fr="Politique de confidentialite",
            content_fr=(
                "DuniaWallet collecte et traite les donnees personnelles conformement "
                "aux lois applicables en matiere de protection des donnees. Nous "
                "collectons votre nom, numero de telephone, informations d'identite "
                "(pour le KYC) et historique des transactions. Ces donnees sont "
                "utilisees uniquement pour fournir nos services, la prevention de la "
                "fraude et la conformite reglementaire. Nous ne vendons pas vos donnees "
                "personnelles a des tiers. Vous avez le droit d'acceder, de corriger "
                "ou de supprimer vos donnees personnelles en contactant notre equipe "
                "de support."
            ),
        ),
    ]
    return {p.topic: p for p in policies}


POLICIES: dict[str, Policy] = _build_policies()


def get_policy(topic: str) -> Policy | None:
    """Retrieve a policy by topic key. Returns None if not found."""
    return POLICIES.get(topic)


def search_policies(query: str) -> list[Policy]:
    """Search policies by keyword across titles and content. Case-insensitive."""
    query_lower = query.lower()
    results: list[Policy] = []
    for policy in POLICIES.values():
        if (
            query_lower in policy.title_en.lower()
            or query_lower in policy.content_en.lower()
            or query_lower in policy.title_fr.lower()
            or query_lower in policy.content_fr.lower()
            or query_lower in policy.topic.lower()
        ):
            results.append(policy)
    return results
