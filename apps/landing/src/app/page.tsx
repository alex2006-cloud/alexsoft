import { Career } from "@/components/Career";
import { Contact } from "@/components/Contact";
import { Expertise } from "@/components/Expertise";
import { Hero } from "@/components/Hero";
import { Lab } from "@/components/Lab";
import { Manifesto } from "@/components/Manifesto";
import { Portfolio } from "@/components/Portfolio";
import { Proof } from "@/components/Proof";
import { Work } from "@/components/Work";

export default function HomePage() {
  return (
    <main id="main">
      <Hero />
      <Proof />
      <Manifesto />
      <Work />
      <Portfolio />
      <Expertise />
      <Lab />
      <Career />
      <Contact />
    </main>
  );
}
