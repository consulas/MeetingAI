"use client";
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { getMeeting, stopMeeting, deleteMeeting, renameMeeting } from '@/lib/api/meeting';
import { Meeting } from '@/lib/api/interface';
import ActionAlert from '@/components/action-alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup} from "@/components/ui/resizable"
import { SidebarTrigger } from '@/components/ui/sidebar';
import Markdown from 'react-markdown'
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { postChat } from '@/lib/api/chat';


export default function MeetingPage() {
  const pathname = usePathname();
  const meetingId = pathname.split('/').pop(); // Extract meeting_id from the path
  const router = useRouter();

  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [newTitle, setNewTitle] = useState(meeting?.title || '');
  const [wordIndex, setWordIndex] = useState<number | null>(null); // State to store wordIndex
  const [response, setResponse] = useState('No response yet');
  const [questionType, setQuestionType] = useState('N/A');
  const [useImage, setUseImage] = useState(false); // State for useImage
  const [useReasoning, setUseReasoning] = useState(false); // State for useReasoning
  const [duration, setDuration] = useState({ hours: 0, minutes: 0, seconds: 0 });

  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [inputText, setInputText] = useState('');

  const liveTranscriptEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!meetingId) return; // Ensure meetingId is available

    // Fetch meeting details using the imported API function
    const fetchMeeting = async () => {
      try {
        const meetingData = await getMeeting(Number(meetingId));
        setMeeting(meetingData);
        setMessages([{
          role: 'system',
          content: 'You are a helpful AI assistant. Please use the following transcript to answer any questions you are asked: ' + meetingData.transcript || 'No transcript available'
        }]);
      } catch (error) {
        console.error('Error fetching meeting:', error);
      }
    };

    fetchMeeting();
  }, [meetingId]);

  useEffect(() => {
    if (meeting?.status === 'ACTIVE' && meetingId) {
      const ws = new WebSocket(`ws://localhost:8080/meetings/${meetingId}`);

      ws.onmessage = (event) => {
        setLiveTranscript(event.data);
      };

      return () => {
        ws.close();
      };
    }
  }, [meeting?.status, meetingId, meeting?.start_time]);

  const handleTitleChange = async () => {
    try {
      const updatedMeeting = await renameMeeting(Number(meetingId), newTitle);
      setMeeting(updatedMeeting);
      setIsEditingTitle(false);
    } catch (error) {
      console.error('Error updating meeting title:', error);
    }
  };

  const handleStopRecording = async () => {
    try {
      await stopMeeting(Number(meetingId));
      location.reload();
    } catch (error) {
      console.error('Error stopping recording:', error);
    }
  };

  const handleDeleteMeeting = async () => {
    try {
      await deleteMeeting(Number(meetingId));
      router.push('/'); // Redirect to the homepage
    } catch (error) {
      console.error('Error deleting meeting:', error);
    }
  };

  // Function to send text to chat endpoint
  const sendToChat = useCallback(async (text: string, use_image: boolean, use_reasoning: boolean, questionType?: string) => {
    const data = await postChat(text, use_image, use_reasoning, questionType)
    setResponse(data.response);
    setQuestionType(data.question_type)
  }, []);

  // Handle word click in transcript
  const handleWordClick = (index: number) => {
    const words = liveTranscript.split(/\s+/);
    if (index >= words.length) return;
    const conversation = words.slice(index).join(' ');
    setWordIndex(index); // Save the wordIndex
    sendToChat(conversation, useImage, useReasoning);
  };

  useEffect(() => {
    const scrollToBottom = () => {
      liveTranscriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    scrollToBottom();
  }, [liveTranscript]);

  const handleButtonClick = (questionType: string) => {
    if (wordIndex !== null) {
      const words = liveTranscript.split(/\s+/);
      const conversation = words.slice(wordIndex).join(' ');
      sendToChat(conversation, useImage, useReasoning, questionType);
    }
  };

  const handleSendMessage = async () => {
    if (inputText.trim() === '') return;

    const newMessage = { role: 'user', content: inputText };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setInputText('');
    console.log(messages)
    try {
      const response = await fetch('http://localhost:8080/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messages: [...messages, newMessage] }),
      });

      const data = await response.json();
      console.log(data)
      const botMessage = { role: 'assistant', content: data };

      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const calculateDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime).getTime();
    const end = endTime ? new Date(endTime).getTime() : new Date().getTime();
    const duration = end - start;
    const hours = Math.floor(duration / 3600000);
    const minutes = Math.floor((duration % 3600000) / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);
    return { hours, minutes, seconds };
  };

  useEffect(() => {
    if (meeting?.status === 'ACTIVE' && meeting.start_time) {
      const interval = setInterval(() => {
        setDuration(calculateDuration(meeting.start_time));
      }, 1000);

      return () => clearInterval(interval);
    } else if (meeting?.end_time && meeting.start_time) {
      setDuration(calculateDuration(meeting.start_time, meeting.end_time));
    }
  }, [meeting?.status, meeting?.start_time, meeting?.end_time]);


  if (!meeting) {
    return <p>Loading meeting details...</p>;
  }

  return (
    <div className="h-screen w-screen">
      <ResizablePanelGroup direction="horizontal" >
        <ResizablePanel defaultSize={75}>
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex justify-between w-full sticky top-0 p-4 z-10 bg-secondary">
              <div className="flex items-center">
                <SidebarTrigger/>
                {isEditingTitle ? (
                <Input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleTitleChange();
                    }
                  }}
                  onBlur={() => setIsEditingTitle(false)}
                  autoFocus
                />
                ) : (
                <h1
                  onClick={() => setIsEditingTitle(true)}
                  className="hover:underline"
                >
                  {meeting.title}
                </h1>
                )}
              </div>

              <ActionAlert
              trigger={
                <Button variant="secondary" className="hover:bg-red-500 border border-primary">
                Delete Meeting
                </Button>
              }
              title="Delete Meeting"
              description="Are you sure you want to delete this meeting? This action cannot be undone."
              actionLabel="Delete"
              onAction={handleDeleteMeeting}
              />
            </div>

            {/* Main Content - Scrollable Area */}
            <div className="flex overflow-y-auto p-2">
              {meeting.status === 'COMPLETED' ? (
                <div>
                  <div className="p-2">
                  <h2 className="font-bold text-2xl">Summary</h2>
                  <div className="markdown">
                    <Markdown>{meeting.summary}</Markdown>
                  </div>
                  {/* <div>{meeting.summary}</div> */}
                  </div>
                  <div className="p-2">
                    <h2 className="font-bold text-2xl">Transcript</h2>
                    <div>
                        {JSON.parse(meeting.transcript).map((entry: any, index: number) => (
                        <React.Fragment key={index}>
                          <p className="font-bold">{entry.speaker}</p>
                          <p>{entry.text}</p>
                        </React.Fragment>
                        ))}
                    </div>
                  </div>
                </div>
              ) : meeting.status === 'ACTIVE' ? (
                <div className="p-2 w-full">
                  <h2 className="font-bold">Transcript</h2>
                  <div>
                    {liveTranscript.split(/\s+/).map((word, index) => (
                      <span
                        key={index}
                        className="hover:bg-secondary cursor-pointer"
                        onClick={() => handleWordClick(index)}
                      >
                        {word}{' '}
                      </span>
                    ))}
                    <div ref={liveTranscriptEndRef} />
                  </div>
                </div>
              ) : (
                <p>Loading meeting information...</p>
              )}
            </div>

            {/* Footer - Stays at bottom */}
            <div className="w-full justify-between flex p-4 bg-secondary mt-auto">
              <div>
                Start Time: {meeting.start_time && new Date(meeting.start_time).toLocaleString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: 'numeric',
                  minute: 'numeric',
                  second: 'numeric',
                  hour12: true,
                })}
              </div>
              
              {meeting.status === 'ACTIVE' ? (
                <>
                  <div>
                    {`${duration.hours} hours, ${duration.minutes} minutes, ${duration.seconds} seconds`}
                  </div>
                  <div>
                    <ActionAlert
                      trigger={
                        <Button variant="secondary" className="hover:bg-red-500 border border-primary">
                          Stop Recording
                        </Button>
                      }
                      title="Stop Recording"
                      description="Are you sure you want to stop recording this meeting?"
                      actionLabel="Stop"
                      onAction={handleStopRecording}
                    />
                  </div>
                </>
              ) : (
                <>
                <div>
                  {`${duration.hours} hours, ${duration.minutes} minutes, ${duration.seconds} seconds`}
                </div>
                <div> 
                  <p>{meeting.audio_file}</p>
                </div>
                </>
              )}
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle />
        <ResizablePanel defaultSize={25}>
            {meeting.status === 'ACTIVE' ? (
            <div className="flex flex-col h-full">
            <div className="overflow-y-auto p-2">
              <div className="markdown">
              <Markdown>
                {response}
              </Markdown>
              </div>
            </div>

            {/* Footer - Stays at bottom */}
            <div className="w-full flex flex-col p-4 bg-secondary mt-auto space-y-4">
              <div className="flex space-x-2">
              <Button variant="secondary" className="hover:bg-blue-500 border border-primary" onClick={() => handleButtonClick('trivia')}>
                Trivia
              </Button>
              <Button variant="secondary" className="hover:bg-blue-500 border border-primary" onClick={() => handleButtonClick('resume')}>
                Resume
              </Button>
              <Button variant="secondary" className="hover:bg-blue-500 border border-primary" onClick={() => handleButtonClick('coding')}>
                Coding
              </Button>
              <Button variant="secondary" className="hover:bg-blue-500 border border-primary" onClick={() => handleButtonClick('system_design')}>
                SysDesign
              </Button>
              <Button variant="secondary" className="hover:bg-blue-500 border border-primary" onClick={() => handleButtonClick('clarify')}>
                Clarify
              </Button>
              </div>
              <div className="flex space-x-4">
              <div className="flex flex-col items-center space-y-1">
                <Label>Image</Label>
                <Switch
                checked={useImage}
                onCheckedChange={() => setUseImage(!useImage)}
                className="data-[state=checked]:bg-blue-500"
                />
              </div>
              <div className="flex flex-col items-center space-y-1">
                <Label>Reasoning</Label>
                <Switch
                checked={useReasoning}
                onCheckedChange={() => setUseReasoning(!useReasoning)}
                className="data-[state=checked]:bg-blue-500"
                />
              </div>
              <div className="space-y-1">
                Last Response Type: {questionType}
              </div>
              </div>
            </div>
            </div>

            ) : (
            <div className="flex flex-col h-full">
              <div className="overflow-y-auto p-2">
              {messages.map((msg, index) => (
                <div key={index} className="p-2 border-b">
                <strong>{msg.role}:</strong> {msg.content}
                </div>
              ))}
              </div>
              <div className="w-full flex p-4 bg-secondary mt-auto">
              <Input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSendMessage();
                }
                }}
                placeholder="Type a message..."
              />
              <Button variant="secondary" className="hover:bg-blue-500 border border-primary" onClick={handleSendMessage}>
                Send
              </Button>
              </div>
            </div>
            )}
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
