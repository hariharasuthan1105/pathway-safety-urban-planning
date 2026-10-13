import { PageHeading, StatusNotice } from '../components/ui/Workstation';
import { CopilotWorkspace } from '../features/copilot/CopilotWorkspace';
export function Copilot(){return <><PageHeading code="07" title="AI Urban Copilot" description="Investigate. Corroborate. Decide with context."/><StatusNotice/><CopilotWorkspace/></>;}
