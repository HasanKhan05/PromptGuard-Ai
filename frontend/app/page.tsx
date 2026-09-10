import { ResearchHeader, ResearchFooter } from "@/components/research/ResearchHeader";
import { HeroSection, ModelTimelineSection, ProtocolSection, ResearchQuestionSection } from "@/components/research/HeroAndMethod";
import { AttackFamiliesSection, CanarySection, FindingGridSection, SecurityUtilitySection } from "@/components/research/ResultsSections";
import { ConclusionSection, DefenseVerdictSection, LimitationsSection } from "@/components/research/ClosingSections";

export default function ResearchWebsite() {
  return (
    <div className="research-site" id="top">
      <div className="aurora aurora-one" aria-hidden="true" />
      <div className="aurora aurora-two" aria-hidden="true" />
      <div className="aurora aurora-three" aria-hidden="true" />
      <ResearchHeader />
      <main className="research-main">
        <HeroSection />
        <ResearchQuestionSection />
        <ProtocolSection />
        <ModelTimelineSection />
        <FindingGridSection />
        <AttackFamiliesSection />
        <CanarySection />
        <SecurityUtilitySection />
        <DefenseVerdictSection />
        <LimitationsSection />
        <ConclusionSection />
      </main>
      <ResearchFooter />
    </div>
  );
}
