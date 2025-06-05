"use client"

import { useState, useEffect } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Plus, Tag as LucideTag, Trash2, ChevronDown, ChevronRight } from "lucide-react";
import { getAudioDevices, getAudioConfigurations } from "@/lib/api/audio";
import { getTags, createTag, deleteTag } from "@/lib/api/tags";
import { AudioDevice, AudioConfig, Tag } from "@/lib/api/interface";
import { createAudioConfiguration } from "@/lib/api/audio"; // Import the API function
import ActionAlert from "@/components/action-alert";
import { getSettings, saveSetting } from '@/lib/api/chat';

export default function SettingsPage() {
  // Tag Settings
  const [tags, setTags] = useState<Tag[]>([]);
  const [newTag, setNewTag] = useState("");
  // Audio Settings
  const [audioDevices, setAudioDevices] = useState<AudioDevice[]>([]);
  const [selectedCompany, setSelectedCompany] = useState("");
  const [selectedDevices, setSelectedDevices] = useState<{ name: string; channel: number }[]>([]);
  const [audioConfigurations, setAudioConfigurations] = useState<AudioConfig[]>([]);
  // AI Settings
  const [resume, setResume] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [monitorNumber, setMonitorNumber] = useState("1");

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        // const [tags, audioDevices, audioConfigurations] = await Promise.all([
        const [tags, audioDevices, audioConfigurations, settings] = await Promise.all([
          getTags(),
          getAudioDevices(),
          getAudioConfigurations(),
          getSettings(),
        ]);

        setTags(tags);

        const devices = Object.entries(audioDevices).map(([name, n_channels]) => ({
          name,
          channel: 0,
          n_channels: Number(n_channels),
        }));
        setAudioDevices(devices);

        setAudioConfigurations(audioConfigurations);

        // Set the resume, jobDescription, and monitorNumber if found
        const settingsMap = new Map(settings.map(setting => [setting.key, setting.value]));
        setResume(settingsMap.get('resume') || '');
        setJobDescription(settingsMap.get('job_description') || '');
        setMonitorNumber(settingsMap.get('monitor_number') || '1');
      } catch (error) {
        console.error('Error fetching initial data:', error);
      }
    };

    fetchInitialData();
  }, []);

  const handleAddTag = async () => {
    if (tags.some(tag => tag.name === newTag.trim())) {
      return;
    }
    try {
      const newTagData = await createTag(newTag);
      setTags((prev) => [...prev, newTagData]);
      setNewTag("");
    } catch (error) {
      console.error("Error adding tag:", error);
    }
  };

  const handleDeleteTag = async (tag: Tag) => {
    try {
      await deleteTag(tag.tag_id);
      setTags((prev) => prev.filter((t) => t.tag_id !== tag.tag_id));
    } catch (error) {
      console.error("Error deleting tag:", error);
    }
  };

  const handleAddDeviceRow = () => {
    setSelectedDevices((prev) => [...prev, { name: "", channel: 0 }]);
  };

  const handleRemoveDeviceRow = (index: number) => {
    setSelectedDevices((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDeviceChange = (index: number, field: "name" | "channel", value: string | number) => {
    setSelectedDevices((prev) =>
      prev.map((device, i) => (i === index ? { ...device, [field]: value } : device))
    );
  };

  const handleSubmit = async () => {
    try {
      const newAudioConfig = await createAudioConfiguration({
        company: selectedCompany,
        devices: selectedDevices.map(device => ({
          name: device.name,
          channel: device.channel,
          n_channels: 1, // Default value or set appropriately
        })),
      });
      // setAudioConfigurations((prev) => [...prev, newAudioConfig]);
      setSelectedCompany('');
      setSelectedDevices([]);
      setAudioConfigurations(await getAudioConfigurations());
    } catch (error) {
      console.error('Error adding audio configuration:', error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && newTag.trim()) {
      handleAddTag();
    }
  };

  return (
    <main className="flex-1 overflow-auto p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Settings</h1>

        <Tabs defaultValue="tags" className="space-y-6">
          <TabsList className="grid grid-cols-3 w-full max-w-md">
            <TabsTrigger value="tags">Tags</TabsTrigger>
            <TabsTrigger value="audio">Audio</TabsTrigger>
            <TabsTrigger value="ai">AI Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="tags">
            <Card>
              <CardHeader>
                <CardTitle>Meeting Tags</CardTitle>
                <CardDescription>Create and manage tags to categorize your meetings.</CardDescription>
              </CardHeader>
              <CardContent>
                <div>
                  <div className="flex justify-between mb-4 gap-2">
                    <Input
                      placeholder="Add new tag"
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyDown={handleKeyDown}
                    />
                    <Button variant="secondary" onClick={handleAddTag} disabled={!newTag.trim()} className="hover:bg-green-500">
                      <Plus/> Add Tag
                    </Button>
                  </div>

                  <div className="border rounded-md p-4">
                    <h3 className="text-sm mb-4">Your Tags</h3>
                    {tags.length > 0 ? (
                      <div className="flex gap-2">
                        {tags.map((tag) => (
                          <Badge key={tag.tag_id} variant="secondary">
                            <LucideTag/> {tag.name}
                            <ActionAlert
                              trigger={
                                <button className="hover:text-red-500">
                                  <Trash2 className="h-3 w-3" />
                                </button>
                              }
                              title="Delete Tag"
                              description="Are you sure you want to delete this tag? This action cannot be undone."
                              actionLabel="Delete"
                              onAction={() => handleDeleteTag(tag)}
                            />
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p>No tags created yet.</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="audio">
            <Card>
              <CardHeader>
                <CardTitle>Audio Settings</CardTitle>
                <CardDescription>Configure your audio input and output devices for meetings.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Enter Company Name"
                      value={selectedCompany}
                      onChange={(e) => setSelectedCompany(e.target.value)}
                    />
                    <Button
                      variant="secondary"
                      onClick={handleSubmit}
                      disabled={!selectedCompany.trim() || selectedDevices.length === 0}
                    >
                      Submit
                    </Button>
                  </div>

                  <div className="space-y-2">
                    {selectedDevices.map((device, index) => (
                      <div key={index} className="flex gap-2 items-center">
                        <Select
                          value={device.name}
                          onValueChange={(value) => handleDeviceChange(index, "name", value)}
                        >
                          <SelectTrigger className="w-64">
                            <SelectValue placeholder="Select Device" />
                          </SelectTrigger>
                          <SelectContent>
                            {audioDevices.map((audioDevice) => (
                              <SelectItem key={audioDevice.name} value={audioDevice.name}>
                                {audioDevice.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        <Select
                          value={device.channel.toString()}
                          onValueChange={(value) => handleDeviceChange(index, "channel", Number(value))}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue placeholder="Select Channel" />
                          </SelectTrigger>
                          <SelectContent>
                            {audioDevices
                              .find((audioDevice) => audioDevice.name === device.name)
                              ?.n_channels &&
                              Array.from(
                                { length: audioDevices.find((audioDevice) => audioDevice.name === device.name)?.n_channels || 0 },
                                (_, i) => i
                              ).map((channel) => (
                                <SelectItem key={channel} value={channel.toString()}>
                                  Channel {channel}
                                </SelectItem>
                              ))}
                          </SelectContent>
                        </Select>

                        <Button variant="secondary" onClick={() => handleRemoveDeviceRow(index)}>
                          Remove
                        </Button>
                      </div>
                    ))}
                  </div>

                  <Button onClick={handleAddDeviceRow} variant="secondary">Add Device</Button>
                </div>

                {audioConfigurations.length > 0 ? (
                  <div className="space-y-2">
                    {audioConfigurations.map((audio) => (
                      <CollapsibleAudioItem key={audio.audio_id} audio={audio} />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm">No audio configurations found.</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ai">
            <Card>
              <CardHeader>
                <CardTitle>AI Settings</CardTitle>
                <CardDescription>
                  Configure the resume, job description, and image context.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Resume</label>
                  <textarea
                    className="w-full p-2 border rounded-md"
                    value={resume}
                    onChange={(e) => setResume(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Job Description</label>
                  <textarea
                    className="w-full p-2 border rounded-md"
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                  />
                </div>
                <div>
                    <label className="block text-sm font-medium mb-2">Monitor Number (number must be &lt;= # of monitors)</label>
                    <p className="text-xs">PSA: It might break the backend if you choose a larger number. Please stick to like 1 or 2, I'm begging you.</p>
                    <input
                    type="number"
                    className="w-full p-2 border rounded-md"
                    value={monitorNumber}
                    onChange={(e) => setMonitorNumber(e.target.value)}
                    />
                  </div>
                <Button variant="secondary" onClick={() => {
                  saveSetting({'key': 'resume', 'value': resume});
                  saveSetting({'key': 'job_description', 'value': jobDescription});
                  saveSetting({'key': 'monitor_number', 'value': monitorNumber});
                }}>
                  Save
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}

function CollapsibleAudioItem({ audio }: { audio: AudioConfig }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border rounded-md p-2">
      <div
        className="flex justify-between"
        onClick={() => setIsOpen(!isOpen)}
      >
        <h3 className="font-semibold">{audio.company}</h3>
        {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </div>
      {isOpen && (
        <div className="mt-2">
          {audio.devices.map((device, index) => (
            <div key={index} className="text-sm">
              <p>
                <strong>Device:</strong> {device.name}
              </p>
              <p>
                <strong>Channel:</strong> {device.channel}
              </p>
              <p>
                <strong>Number of Channels:</strong> {device.n_channels}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
