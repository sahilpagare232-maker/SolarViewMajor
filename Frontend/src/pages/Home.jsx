import { Link } from "react-router-dom";
import "./SolarView.css";

const steps = [
  { number: "01", title: "Find your location", text: "Search a city, street, or address on the interactive map." },
  { number: "02", title: "Select an area", text: "Draw a rectangle around the buildings you want to assess." },
  { number: "03", title: "Explore the results", text: "Review building footprints, usable roof estimates, and panel layouts." },
];

export default function Home() {
  return <main className="solar-page home-page">
    <header className="topbar"><Link className="brand" to="/" aria-label="SolarView home"><span className="brand-mark">☀</span> SolarView</Link><span className="topbar-note">Solar potential explorer</span></header>
    <section className="hero-section">
      <div className="hero-copy"><p className="eyebrow">ROOFTOP SOLAR, MADE VISIBLE</p><h1>See the solar potential<br />above your neighborhood.</h1><p className="hero-description">Explore real building footprints, estimate usable rooftop area, and preview a solar panel layout on an interactive map.</p><Link className="button button-primary hero-cta" to="/map">Start exploring <span aria-hidden="true">→</span></Link><p className="hero-caption"><span className="sun-mini">☀</span> OpenStreetMap building data · Clear estimates</p></div>
      <div className="hero-art" aria-hidden="true"><div className="sun-disc" /><div className="solar-roof"><div className="roof-top"><div className="roof-panels">{Array.from({ length: 12 }, (_, i) => <span key={i} />)}</div></div><div className="roof-front"><div className="window-row"><i /><i /><i /></div><div className="window-row"><i /><i /><i /></div><div className="door" /></div></div><div className="floating-chip"><span className="chip-spark">✦</span><span><strong>Solar ready</strong><small>Explore a selected area</small></span></div><div className="art-ground" /></div>
    </section>
    <section className="steps-section"><div className="steps-heading"><div><p className="eyebrow">HOW IT WORKS</p><h2>From map to insight in three steps</h2></div><p>Choose a place and see what the rooftops could support.</p></div><div className="steps-grid">{steps.map((step) => <article className="step-card" key={step.number}><span>{step.number}</span><h3>{step.title}</h3><p>{step.text}</p></article>)}</div></section>
    <footer className="home-footer">SolarView provides exploratory estimates. Energy values use synthetic demo irradiance and are not a site survey.</footer>
  </main>;
}
