import { ChatShell } from "../ChatShell";

export default async function ChatPage({
  params,
}: {
  params: Promise<{ conversationId?: string[] }>;
}) {
  const { conversationId } = await params;
  const id = conversationId?.[0];
  return <ChatShell initialConversationId={id ? Number(id) : null} />;
}
