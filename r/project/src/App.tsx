import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Loader2, ChevronLeft, ChevronRight, SkipBack, SkipForward, Link, Copy, Check, Sunrise, Sunset } from 'lucide-react';
import SunCalc from 'suncalc';
import { locationCoordinates } from './config/locations';

interface VideoData {
  id: string;
  timestamp: string;
  url: string;
  location: string;
}

const App: React.FC = () => {
  const [videos, setVideos] = useState<VideoData[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [responseData, setResponseData] = useState<any>(null);
  const [responseInfo, setResponseInfo] = useState<any>(null);
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  const [locations, setLocations] = useState<string[]>([]);
  const [showUrl, setShowUrl] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchVideos();
  }, []);

  useEffect(() => {
    if (videos.length > 0) {
      const sortedVideos = [...videos].sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
      setSelectedVideo(sortedVideos[0]);
    }
  }, [videos]);

  const fetchVideos = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const response = await fetch('https://weather.fogcat5.com/collector/api', {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'Origin': window.location.origin
        }
      });

      clearTimeout(timeoutId);
      
      // Capture response information
      const responseInfo = {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        headers: Object.fromEntries([...response.headers.entries()]),
        type: response.type,
        url: response.url
      };
      setResponseInfo(responseInfo);

      let data;
      try {
        const text = await response.text(); // First get the raw text
        console.log('Raw response:', text); // Log the raw response
        setResponseData(text); // Store the raw response
        
        try {
          data = JSON.parse(text); // Then try to parse it
        } catch (parseError) {
          console.error('Parse error:', parseError);
          throw new Error(`Failed to parse JSON: ${text.substring(0, 200)}...`);
        }
      } catch (textError) {
        console.error('Text error:', textError);
        throw new Error(`Failed to read response: ${textError.message}`);
      }
      
      if (!Array.isArray(data)) {
        throw new Error(`Invalid response format. Received: ${typeof data}`);
      }

      const sortedData = data.sort((a: VideoData, b: VideoData) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );

      setVideos(sortedData);
      const uniqueLocations = [...new Set(sortedData.map((video: VideoData) => video.location))];
      setLocations(uniqueLocations);
      setError(null);
      setResponseData(null);
      setResponseInfo(null);
      setLoading(false);
    } catch (err) {
      console.error('Fetch error:', err); // Log the full error
      const errorMessage = err instanceof Error 
        ? `${err.name}: ${err.message}`
        : 'An unexpected error occurred. Please try again later.';
      
      setError(errorMessage);
      setLoading(false);
    }
  };

  const navigateToAdjacentDay = (direction: 'previous' | 'next') => {
    if (!selectedVideo) return;

    const filteredVideos = getFilteredVideos();
    const currentDate = new Date(selectedVideo.timestamp);
    currentDate.setHours(0, 0, 0, 0);

    let targetVideo: VideoData | undefined;

    if (direction === 'previous') {
      targetVideo = filteredVideos.find(video => {
        const videoDate = new Date(video.timestamp);
        videoDate.setHours(0, 0, 0, 0);
        return videoDate.getTime() < currentDate.getTime();
      });
    } else {
      targetVideo = filteredVideos.reverse().find(video => {
        const videoDate = new Date(video.timestamp);
        videoDate.setHours(0, 0, 0, 0);
        return videoDate.getTime() > currentDate.getTime();
      });
    }

    if (targetVideo) {
      setSelectedVideo(targetVideo);
    }
  };

  const navigateToAdjacentVideo = (direction: 'previous' | 'next') => {
    if (!selectedVideo) return;

    const filteredVideos = getFilteredVideos();
    const currentIndex = filteredVideos.findIndex(v => v.id === selectedVideo.id);
    
    if (direction === 'previous' && currentIndex > 0) {
      setSelectedVideo(filteredVideos[currentIndex - 1]);
    } else if (direction === 'next' && currentIndex < filteredVideos.length - 1) {
      setSelectedVideo(filteredVideos[currentIndex + 1]);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const getFilteredVideos = () => {
    return videos.filter(video => 
      selectedLocation ? video.location === selectedLocation : true
    ).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  };

  const formatDateTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSunTimes = (timestamp: string, location: string) => {
    const date = new Date(timestamp);
    const coordinates = locationCoordinates[location];
    
    if (!coordinates) return null;

    const times = SunCalc.getTimes(date, coordinates.lat, coordinates.lng);
    return {
      sunrise: times.sunrise.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      sunset: times.sunset.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading videos...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded-lg shadow-sm max-w-md w-full" role="alert">
          <strong className="font-bold block mb-2">Error: </strong>
          <span className="block mb-4">{error}</span>
          
          {responseInfo && (
            <div className="mb-4">
              <p className="font-bold mb-2">Response Details:</p>
              <pre className="bg-red-50 p-3 rounded text-sm overflow-auto max-h-48">
                {JSON.stringify(responseInfo, null, 2)}
              </pre>
            </div>
          )}
          
          {responseData && (
            <div className="mb-4">
              <p className="font-bold mb-2">Response Data:</p>
              <pre className="bg-red-50 p-3 rounded text-sm overflow-auto max-h-48">
                {responseData}
              </pre>
            </div>
          )}
          
          <button
            onClick={() => {
              setLoading(true);
              setError(null);
              setResponseData(null);
              setResponseInfo(null);
              fetchVideos();
            }}
            className="w-full bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded transition-colors duration-200"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Weather Video Archive</h1>
          
          <div className="flex flex-col sm:flex-row gap-4">
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Locations</option>
              {locations.map(location => (
                <option key={location} value={location}>{location}</option>
              ))}
            </select>
            
            <button
              onClick={() => {
                setLoading(true);
                fetchVideos();
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200 shadow-sm"
            >
              Refresh
            </button>
          </div>
        </header>

        {selectedVideo && (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden mb-8">
            <div className="aspect-w-16 aspect-h-9">
              <video
                key={selectedVideo.url}
                controls
                className="w-full h-full object-contain"
              >
                <source src={selectedVideo.url} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>

            <div className="p-4 border-t">
              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-4">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span>{formatDateTime(selectedVideo.timestamp)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  <span>{selectedVideo.location}</span>
                </div>
                {locationCoordinates[selectedVideo.location] && (
                  <div className="flex items-center gap-4">
                    {getSunTimes(selectedVideo.timestamp, selectedVideo.location) && (
                      <>
                        <div className="flex items-center gap-2">
                          <Sunrise className="w-4 h-4 text-orange-500" />
                          <span>{getSunTimes(selectedVideo.timestamp, selectedVideo.location)?.sunrise}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Sunset className="w-4 h-4 text-orange-500" />
                          <span>{getSunTimes(selectedVideo.timestamp, selectedVideo.location)?.sunset}</span>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => navigateToAdjacentDay('previous')}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200"
                >
                  <SkipBack className="w-4 h-4" />
                  <span>Previous Day</span>
                </button>
                
                <button
                  onClick={() => navigateToAdjacentVideo('previous')}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Previous</span>
                </button>
                
                <button
                  onClick={() => navigateToAdjacentVideo('next')}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200"
                >
                  <span>Next</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
                
                <button
                  onClick={() => navigateToAdjacentDay('next')}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200"
                >
                  <span>Next Day</span>
                  <SkipForward className="w-4 h-4" />
                </button>

                <button
                  onClick={() => setShowUrl(!showUrl)}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200 ml-auto"
                >
                  <Link className="w-4 h-4" />
                  <span>{showUrl ? 'Hide URL' : 'Show URL'}</span>
                </button>
              </div>

              {showUrl && (
                <div className="mt-4 flex items-center gap-2">
                  <input
                    type="text"
                    value={selectedVideo.url}
                    readOnly
                    className="flex-1 px-3 py-2 bg-gray-50 border rounded-lg"
                  />
                  <button
                    onClick={() => copyToClipboard(selectedVideo.url)}
                    className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200"
                  >
                    {copied ? (
                      <>
                        <Check className="w-4 h-4 text-green-500" />
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;